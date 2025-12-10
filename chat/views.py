from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from accounts.models import StudentProfile
from .models import ChatRequest, ChatRoom, Message, Call
from .forms import ChatRequestForm

@login_required
def send_chat_request(request, recipient_id):
    """Send a chat request to another student"""
    try:
        sender_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'You must have a student profile to send chat requests.'}, status=400)
    
    recipient_profile = get_object_or_404(StudentProfile, id=recipient_id, is_active=True)
    
    # Check if user is trying to send to themselves
    if sender_profile == recipient_profile:
        return JsonResponse({'error': 'You cannot send a chat request to yourself.'}, status=400)
    
    if request.method == 'POST':
        form = ChatRequestForm(request.POST, sender=sender_profile, recipient=recipient_profile)
        if form.is_valid():
            chat_request = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Chat request sent to {recipient_profile.name} successfully!',
                'request_id': chat_request.id
            })
        else:
            # Return form errors
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
            return JsonResponse({'error': 'Validation failed', 'errors': errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def chat_request_list(request):
    """View all chat requests (sent and received)"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must have a student profile to view chat requests.')
        return redirect('accounts:profile')
    
    # Get sent and received requests
    sent_requests = ChatRequest.objects.filter(sender=profile).select_related('recipient')
    received_requests = ChatRequest.objects.filter(recipient=profile).select_related('sender')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        sent_requests = sent_requests.filter(status=status_filter)
        received_requests = received_requests.filter(status=status_filter)
    
    context = {
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'status_filter': status_filter,
        'status_choices': ChatRequest.STATUS_CHOICES,
    }
    
    return render(request, 'chat/request_list.html', context)

@login_required
def accept_chat_request(request, request_id):
    """Accept a chat request and create a chat room"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=400)
    
    chat_request = get_object_or_404(ChatRequest, id=request_id, recipient=profile)
    
    if not chat_request.can_be_accepted():
        return JsonResponse({'error': 'This request cannot be accepted.'}, status=400)
    
    if request.method == 'POST':
        chat_request.status = 'accepted'
        chat_request.save()
        
        # Create or get chat room
        room_name = ChatRoom.generate_room_name(
            chat_request.sender.id,
            chat_request.recipient.id
        )
        
        chat_room, created = ChatRoom.objects.get_or_create(
            room_name=room_name,
            defaults={
                'participant1': chat_request.sender,
                'participant2': chat_request.recipient,
                'chat_request': chat_request,
            }
        )
        
        # If room already existed, link the request to it
        if not created and not chat_room.chat_request:
            chat_room.chat_request = chat_request
            chat_room.is_active = True
            chat_room.save()
        
        # Create initial message from the chat request if this is a new room
        if created:
            Message.objects.create(
                room=chat_room,
                sender=chat_request.sender,
                content=f"Chat request: {chat_request.message}"
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Chat request from {chat_request.sender.name} accepted!',
            'room_id': chat_room.id,
            'room_name': chat_room.room_name
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def reject_chat_request(request, request_id):
    """Reject a chat request"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=400)
    
    chat_request = get_object_or_404(ChatRequest, id=request_id, recipient=profile)
    
    if not chat_request.can_be_accepted():
        return JsonResponse({'error': 'This request cannot be rejected.'}, status=400)
    
    if request.method == 'POST':
        chat_request.status = 'rejected'
        chat_request.save()
        return JsonResponse({
            'success': True,
            'message': 'Chat request rejected.'
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def cancel_chat_request(request, request_id):
    """Cancel a sent chat request"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=400)
    
    chat_request = get_object_or_404(ChatRequest, id=request_id, sender=profile)
    
    if not chat_request.can_be_cancelled():
        return JsonResponse({'error': 'This request cannot be cancelled.'}, status=400)
    
    if request.method == 'POST':
        chat_request.status = 'cancelled'
        chat_request.save()
        return JsonResponse({
            'success': True,
            'message': 'Chat request cancelled.'
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def check_pending_request(request, recipient_id):
    """Check if there's a pending request between current user and recipient"""
    try:
        sender_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'has_pending': False})
    
    recipient_profile = get_object_or_404(StudentProfile, id=recipient_id, is_active=True)
    
    pending_request = ChatRequest.objects.filter(
        sender=sender_profile,
        recipient=recipient_profile,
        status='pending'
    ).first()
    
    if pending_request:
        return JsonResponse({
            'has_pending': True,
            'request_id': pending_request.id,
            'message': pending_request.message,
            'created_at': pending_request.created_at.isoformat()
        })
    
    return JsonResponse({'has_pending': False})

@login_required
def chat_room_list(request):
    """List all active chat rooms for the current user"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must have a student profile to view chats.')
        return redirect('accounts:profile')
    
    # Get pending incoming chat requests
    incoming_requests = ChatRequest.objects.filter(
        recipient=profile,
        status='pending'
    ).select_related('sender').order_by('-created_at')
    
    # Get all chat rooms where user is a participant
    chat_rooms = ChatRoom.objects.filter(
        Q(participant1=profile) | Q(participant2=profile),
        is_active=True
    ).select_related('participant1', 'participant2').annotate(
        last_message_time=Max('messages__timestamp')
    ).order_by('-updated_at')
    
    # Add unread counts and last message for each room
    for room in chat_rooms:
        room.other_participant = room.get_other_participant(profile)
        room.unread_count = room.get_unread_count(profile)
        room.last_message = room.messages.order_by('-timestamp').first()
    
    return render(request, 'chat/room_list.html', {
        'chat_rooms': chat_rooms,
        'incoming_requests': incoming_requests,
        'profile': profile
    })

@login_required
def chat_room_detail(request, room_name):
    """View a specific chat room"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must have a student profile to chat.')
        return redirect('accounts:profile')
    
    chat_room = get_object_or_404(ChatRoom, room_name=room_name, is_active=True)
    
    # Verify user is a participant
    if not chat_room.has_participant(profile):
        messages.error(request, 'You do not have access to this chat room.')
        return redirect('chat:room_list')
    
    # Get the other participant
    other_participant = chat_room.get_other_participant(profile)
    
    # Get messages (last 50, can be paginated later)
    messages_list = chat_room.messages.select_related('sender').order_by('timestamp')[:50]
    
    # Mark messages as read
    unread_messages = chat_room.messages.filter(
        is_read=False
    ).exclude(sender=profile)
    
    for msg in unread_messages:
        msg.mark_as_read()
    
    return render(request, 'chat/room_detail.html', {
        'chat_room': chat_room,
        'other_participant': other_participant,
        'messages': messages_list,
        'profile': profile
    })

@login_required
def send_message(request, room_name):
    """Send a message via HTTP POST (always works, even without WebSocket)"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'You must have a student profile to send messages.'}, status=400)
    
    chat_room = get_object_or_404(ChatRoom, room_name=room_name, is_active=True)
    
    # Verify user is a participant
    if not chat_room.has_participant(profile):
        return JsonResponse({'error': 'You do not have access to this chat room.'}, status=403)
    
    if request.method == 'POST':
        message_content = request.POST.get('message', '').strip()
        
        if not message_content:
            return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
        
        if len(message_content) > 2000:
            return JsonResponse({'error': 'Message is too long (max 2000 characters).'}, status=400)
        
        # Save message to database
        message = Message.objects.create(
            room=chat_room,
            sender=profile,
            content=message_content
        )
        
        # Update room's updated_at timestamp
        chat_room.save()
        
        # Broadcast message via WebSocket channel layer (for real-time delivery)
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                room_group_name = f'chat_{room_name}'
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        'username': request.user.username,
                        'sender_name': profile.name,
                        'sender_id': profile.id,
                        'timestamp': message.timestamp.isoformat(),
                        'message_id': message.id,
                    }
                )
        except Exception as e:
            # If channel layer fails, message is still saved - just log the error
            print(f"Failed to broadcast message via WebSocket: {e}")
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'message': message_content,
            'timestamp': message.timestamp.isoformat(),
            'sender_id': profile.id,
            'sender_name': profile.name
        })
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def get_new_messages(request, room_name):
    """Get new messages since a given timestamp (for polling when WebSocket is unavailable)"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    chat_room = get_object_or_404(ChatRoom, room_name=room_name, is_active=True)
    
    # Verify user is a participant
    if not chat_room.has_participant(profile):
        return JsonResponse({'error': 'Access denied.'}, status=403)
    
    # Get timestamp from query parameter (optional)
    since = request.GET.get('since')
    
    if since:
        from django.utils.dateparse import parse_datetime
        try:
            since_dt = parse_datetime(since)
            new_messages = chat_room.messages.filter(
                timestamp__gt=since_dt
            ).exclude(sender=profile).select_related('sender').order_by('timestamp')
        except (ValueError, TypeError):
            new_messages = chat_room.messages.exclude(sender=profile).select_related('sender').order_by('-timestamp')[:10]
    else:
        # Get last 10 messages
        new_messages = chat_room.messages.exclude(sender=profile).select_related('sender').order_by('-timestamp')[:10]
    
    # Mark as read
    for msg in new_messages:
        if not msg.is_read:
            msg.mark_as_read()
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.name,
        'timestamp': msg.timestamp.isoformat(),
    } for msg in reversed(new_messages)]  # Reverse to get chronological order
    
    return JsonResponse({
        'messages': messages_data,
        'count': len(messages_data)
    })

# Call-related views

@login_required
def initiate_call(request, room_name):
    """Initiate a voice/video call in a chat room"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    chat_room = get_object_or_404(ChatRoom, room_name=room_name, is_active=True)
    
    # Verify user is a participant
    if not chat_room.has_participant(profile):
        return JsonResponse({'error': 'Access denied.'}, status=403)
    
    # GET request - check for active calls
    if request.method == 'GET':
        active_call = Call.objects.filter(
            chat_room=chat_room,
            status__in=['initiated', 'ringing', 'accepted']
        ).first()
        
        if active_call:
            # Return info about the active call
            return JsonResponse({
                'active_call': {
                    'call_id': active_call.id,
                    'call_type': active_call.call_type,
                    'caller_name': active_call.caller.name,
                    'status': active_call.status
                }
            })
        else:
            return JsonResponse({'active_call': None})
    
    # POST request - initiate a new call
    if request.method == 'POST':
        call_type = request.POST.get('call_type', 'video')
        
        if call_type not in ['audio', 'video']:
            return JsonResponse({'error': 'Invalid call type.'}, status=400)
        
        # Get the other participant
        other_participant = chat_room.get_other_participant(profile)
        
        # Check if there's already an active call in this room
        active_call = Call.objects.filter(
            chat_room=chat_room,
            status__in=['initiated', 'ringing', 'accepted']
        ).first()
        
        if active_call:
            return JsonResponse({'error': 'There is already an active call in this room.'}, status=400)
        
        # Create the call
        call = Call.objects.create(
            caller=profile,
            receiver=other_participant,
            chat_room=chat_room,
            call_type=call_type,
            status='initiated'
        )
        
        return JsonResponse({
            'success': True,
            'call_id': call.id,
            'call_type': call_type,
            'receiver_name': other_participant.name,
            'message': f'{call_type.capitalize()} call initiated'
        })
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def end_call(request, call_id):
    """End an active call"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    call = get_object_or_404(Call, id=call_id)
    
    # Verify user is part of this call
    if call.caller != profile and call.receiver != profile:
        return JsonResponse({'error': 'Access denied.'}, status=403)
    
    if request.method == 'POST':
        from django.utils import timezone
        
        # Only end if call is active
        if call.status in ['initiated', 'ringing', 'accepted']:
            call.ended_at = timezone.now()
            call.status = 'ended'
            
            # Calculate duration if call was accepted
            if call.status == 'accepted' and call.accepted_at:
                call.calculate_duration()
            
            call.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Call ended',
                'duration': call.get_duration_display()
            })
        else:
            return JsonResponse({'error': 'Call is not active.'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def accept_call(request, call_id):
    """Accept an incoming call"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    call = get_object_or_404(Call, id=call_id)
    
    # Verify user is the receiver
    if call.receiver != profile:
        return JsonResponse({'error': 'You are not the receiver of this call.'}, status=403)
    
    if request.method == 'POST':
        if call.can_be_answered():
            from django.utils import timezone
            call.status = 'accepted'
            call.accepted_at = timezone.now()
            call.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Call accepted',
                'call_id': call.id
            })
        else:
            return JsonResponse({'error': 'Call cannot be answered.'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def reject_call(request, call_id):
    """Reject an incoming call"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    call = get_object_or_404(Call, id=call_id)
    
    # Verify user is the receiver
    if call.receiver != profile:
        return JsonResponse({'error': 'You are not the receiver of this call.'}, status=403)
    
    if request.method == 'POST':
        if call.can_be_answered():
            from django.utils import timezone
            call.status = 'rejected'
            call.ended_at = timezone.now()
            call.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Call rejected'
            })
        else:
            return JsonResponse({'error': 'Call cannot be rejected.'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def cancel_call(request, call_id):
    """Cancel an outgoing call before it's answered"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    call = get_object_or_404(Call, id=call_id)
    
    # Verify user is the caller
    if call.caller != profile:
        return JsonResponse({'error': 'You are not the caller of this call.'}, status=403)
    
    if request.method == 'POST':
        if call.can_be_answered():
            from django.utils import timezone
            call.status = 'cancelled'
            call.ended_at = timezone.now()
            call.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Call cancelled'
            })
        else:
            return JsonResponse({'error': 'Call cannot be cancelled.'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def call_history(request):
    """View call history for the current user"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must have a student profile to view call history.')
        return redirect('accounts:profile')
    
    # Get active calls (initiated, ringing, or accepted)
    active_calls = Call.objects.filter(
        Q(caller=profile) | Q(receiver=profile),
        status__in=['initiated', 'ringing', 'accepted']
    ).select_related('caller', 'receiver', 'chat_room').order_by('-initiated_at')
    
    # Get all past calls (ended, rejected, missed, cancelled)
    past_calls = Call.objects.filter(
        Q(caller=profile) | Q(receiver=profile),
        status__in=['ended', 'rejected', 'missed', 'cancelled']
    ).select_related('caller', 'receiver', 'chat_room').order_by('-initiated_at')[:50]
    
    # Add additional info for each call
    for call in active_calls:
        call.other_user = call.receiver if call.caller == profile else call.caller
        call.is_outgoing = call.caller == profile
    
    for call in past_calls:
        call.other_user = call.receiver if call.caller == profile else call.caller
        call.is_outgoing = call.caller == profile
    
    return render(request, 'chat/call_history.html', {
        'active_calls': active_calls,
        'calls': past_calls,
        'profile': profile
    })

@login_required
def get_call_status(request, call_id):
    """Get current status of a call (for polling)"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found.'}, status=400)
    
    call = get_object_or_404(Call, id=call_id)
    
    # Verify user is part of this call
    if call.caller != profile and call.receiver != profile:
        return JsonResponse({'error': 'Access denied.'}, status=403)
    
    return JsonResponse({
        'call_id': call.id,
        'status': call.status,
        'call_type': call.call_type,
        'is_active': call.is_active(),
        'duration': call.get_duration_display() if call.duration_seconds else None
    })

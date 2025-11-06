from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max
from accounts.models import StudentProfile
from .models import ChatRequest, ChatRoom, Message
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

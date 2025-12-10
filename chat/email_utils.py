"""
Email notification utilities for call system.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_call_notification_email(call, notification_type='initiated'):
    """
    Send email notification for a call.
    
    Args:
        call: Call model instance
        notification_type: 'initiated', 'accepted', 'rejected', 'cancelled'
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        caller_name = call.caller.name
        caller_email = call.caller.user.email
        receiver_name = call.receiver.name
        receiver_email = call.receiver.user.email
        call_type = call.get_call_type_display()
        
        if notification_type == 'initiated':
            # Email to receiver
            subject = f"📞 {caller_name} is inviting you to a {call_type}"
            message = f"""
Hi {receiver_name},

{caller_name} has invited you to a {call_type} call on StudyIt!

Join the call using this Google Meet link:
{call.meet_link}

Call Details:
- Type: {call_type}
- Initiated: {call.initiated_at.strftime('%B %d, %Y at %I:%M %p')}
- From: {caller_name}

You can accept or reject this call invitation from your StudyIt dashboard.

Best regards,
StudyIt Team
            """
            recipient_list = [receiver_email]
            
        elif notification_type == 'accepted':
            # Email to caller
            subject = f"✅ {receiver_name} accepted your {call_type} call"
            message = f"""
Hi {caller_name},

Great news! {receiver_name} has accepted your {call_type} call invitation.

Join the call using this Google Meet link:
{call.meet_link}

Call Details:
- Type: {call_type}
- Accepted: {call.accepted_at.strftime('%B %d, %Y at %I:%M %p') if call.accepted_at else 'Just now'}
- With: {receiver_name}

Best regards,
StudyIt Team
            """
            recipient_list = [caller_email]
            
        elif notification_type == 'rejected':
            # Email to caller
            subject = f"❌ {receiver_name} declined your {call_type} call"
            message = f"""
Hi {caller_name},

{receiver_name} has declined your {call_type} call invitation.

You can send another call invitation later from your chat with {receiver_name}.

Best regards,
StudyIt Team
            """
            recipient_list = [caller_email]
            
        elif notification_type == 'cancelled':
            # Email to receiver
            subject = f"🚫 {caller_name} cancelled the {call_type} call"
            message = f"""
Hi {receiver_name},

{caller_name} has cancelled the {call_type} call invitation.

Best regards,
StudyIt Team
            """
            recipient_list = [receiver_email]
            
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False
        
        # Send the email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True,  # Don't raise exceptions if email fails
            )
            
            # Update call email tracking
            if notification_type == 'initiated':
                call.email_sent = True
                call.email_sent_at = timezone.now()
                call.save(update_fields=['email_sent', 'email_sent_at'])
            
            logger.info(f"Sent {notification_type} email for call {call.id} to {recipient_list}")
            return True
        except Exception as email_error:
            logger.warning(f"Email sending failed but continuing: {email_error}")
            return False
        
    except Exception as e:
        logger.error(f"Error in send_call_notification_email: {e}")
        return False

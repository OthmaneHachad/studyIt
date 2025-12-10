"""
Simple test script to debug call creation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyit_project.settings')
django.setup()

from chat.models import Call, ChatRoom
from accounts.models import StudentProfile
from chat.google_meet import create_google_meet_event
from chat.email_utils import send_call_notification_email

def test_call_creation():
    print("=" * 50)
    print("Testing Call Creation Flow")
    print("=" * 50)
    
    # Get first two users
    try:
        profiles = StudentProfile.objects.all()[:2]
        if len(profiles) < 2:
            print("ERROR: Need at least 2 user profiles")
            return
        
        profile1 = profiles[0]
        profile2 = profiles[1]
        print(f"✓ Found users: {profile1.name} and {profile2.name}")
    except Exception as e:
        print(f"✗ Error getting profiles: {e}")
        return
    
    # Get or create chat room
    try:
        room_name = ChatRoom.generate_room_name(profile1.id, profile2.id)
        chat_room, created = ChatRoom.objects.get_or_create(
            room_name=room_name,
            defaults={
                'participant1': profile1,
                'participant2': profile2
            }
        )
        print(f"✓ Chat room: {chat_room.room_name}")
    except Exception as e:
        print(f"✗ Error with chat room: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test Google Meet creation
    try:
        meet_data = create_google_meet_event(
            caller_name=profile1.name,
            caller_email=profile1.user.email,
            receiver_name=profile2.name,
            receiver_email=profile2.user.email,
            call_type='video'
        )
        print(f"✓ Meet link created: {meet_data['meet_link']}")
    except Exception as e:
        print(f"✗ Error creating Meet link: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test Call model creation
    try:
        call = Call.objects.create(
            caller=profile1,
            receiver=profile2,
            chat_room=chat_room,
            call_type='video',
            status='initiated',
            meet_link=meet_data.get('meet_link'),
            calendar_event_id=meet_data.get('event_id')
        )
        print(f"✓ Call created: ID={call.id}")
    except Exception as e:
        print(f"✗ Error creating Call: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test email sending
    try:
        email_sent = send_call_notification_email(call, notification_type='initiated')
        print(f"✓ Email sent: {email_sent}")
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)

if __name__ == '__main__':
    test_call_creation()

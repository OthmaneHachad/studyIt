from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import StudentProfile
from .models import StudySession, SessionEnrollment
from .models import StudySession, SessionEnrollment

class SessionListStatusTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Host User
        self.host_user = User.objects.create_user(username='host', password='password')
        
        self.session = StudySession.objects.create(
            host=self.host_user,
            title="Review Session",
            location="Library",
            room_number="304",
            start_time=timezone.now() + timezone.timedelta(hours=1),
            end_time=timezone.now() + timezone.timedelta(hours=2)
        )
        
        # Create Student
        self.student_user = User.objects.create_user(username='student', password='password')
        self.student_profile = StudentProfile.objects.create(user=self.student_user, name="Student Name", year="sophomore")

    def test_session_list_shows_status(self):
        self.client.force_login(self.student_user)
        
        # 1. No enrollment -> Status should be None
        response = self.client.get(reverse('study_sessions:session_list'))
        session_obj = response.context['sessions'][0]
        self.assertIsNone(session_obj.user_status)
        
        # 2. Pending enrollment
        enrollment = SessionEnrollment.objects.create(
            session=self.session, 
            student=self.student_profile,
            status='pending'
        )
        
        response = self.client.get(reverse('study_sessions:session_list'))
        session_obj = response.context['sessions'][0]
        self.assertEqual(session_obj.user_status, 'pending')
        
        # 3. Approved enrollment
        enrollment.status = 'approved'
        enrollment.save()
        
        response = self.client.get(reverse('study_sessions:session_list'))
        session_obj = response.context['sessions'][0]
        self.assertEqual(session_obj.user_status, 'approved')

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import TAProfile
from .forms import StudySessionForm
from .models import StudySession


def session_list(request):
    """Public list of upcoming/active study sessions."""
    now = timezone.now()
    sessions = list(
        StudySession.objects.filter(is_active=True, end_time__gte=now)
        .select_related("host", "location")
        .order_by("start_time")
    )
    
    can_post = request.user.is_authenticated
    
    # helper for checking enrollment status
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        from .models import SessionEnrollment
        enrollments = {
            e.session_id: e.status 
            for e in SessionEnrollment.objects.filter(student=request.user.student_profile)
        }
        for session in sessions:
            session.user_status = enrollments.get(session.id)
            
    return render(
        request,
        "study_sessions/session_list.html",
        {"sessions": sessions, "can_post": can_post},
    )


@login_required
def session_create(request):
    """Allow TA/session hosts to post new study sessions."""
    ta_profile = getattr(request.user, "ta_profile", None)
    if ta_profile is None:
        # Auto-create TA profile for users who signed up as TA
        full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        ta_profile = TAProfile.objects.create(
            user=request.user,
            name=full_name,
            department="",
            is_active=True,
        )
        messages.info(request, "TA profile created for you. You can now post sessions.")

    if request.method == "POST":
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.host = ta_profile
            session.save()
            messages.success(request, "Study session posted successfully.")
            return redirect("study_sessions:session_list")
    else:
        form = StudySessionForm()

    return render(request, "study_sessions/session_form.html", {"form": form})


@login_required
def request_session_join(request, session_id):
    """Allow a student to request to join a session."""
    session = get_object_or_404(StudySession, id=session_id)
    student_profile = getattr(request.user, "student_profile", None)

    if not student_profile:
        messages.error(request, "You must be a student to join a session.")
        return redirect("study_sessions:session_list")

    if session.host.user == request.user:
        messages.error(request, "You cannot join your own session.")
        return redirect("study_sessions:session_list")

    # Check if already requested/enrolled
    from .models import SessionEnrollment

    enrollment, created = SessionEnrollment.objects.get_or_create(
        session=session, student=student_profile
    )

    if created:
        messages.success(request, "Request to join sent successfully!")
    else:
        messages.info(request, f"You have already requested to join (Status: {enrollment.status}).")

    return redirect("study_sessions:session_list")


@login_required
def manage_session_requests(request, session_id):
    """Allow host to view and manage requests for their session."""
    session = get_object_or_404(StudySession, id=session_id)

    if session.host.user != request.user:
        messages.error(request, "You do not have permission to manage this session.")
        return redirect("study_sessions:session_list")

    enrollments = session.enrollments.select_related("student").order_by("created_at")

    return render(
        request,
        "study_sessions/manage_requests.html",
        {"session": session, "enrollments": enrollments},
    )


@login_required
def update_request_status(request, enrollment_id, action):
    """Approve or reject a request."""
    from .models import SessionEnrollment

    enrollment = get_object_or_404(SessionEnrollment, id=enrollment_id)

    # Verify that the logged-in user is the host of the session
    if enrollment.session.host.user != request.user:
        messages.error(request, "Permission denied.")
        return redirect("study_sessions:session_list")

    if action == "approve":
        enrollment.status = "approved"
        messages.success(request, f"Approved {enrollment.student.name}'s request.")
    elif action == "reject":
        enrollment.status = "rejected"
        messages.success(request, f"Rejected {enrollment.student.name}'s request.")
    else:
        messages.error(request, "Invalid action.")
        return redirect("study_sessions:manage_requests", session_id=enrollment.session.id)
    
    enrollment.save()
    return redirect("study_sessions:manage_requests", session_id=enrollment.session.id)

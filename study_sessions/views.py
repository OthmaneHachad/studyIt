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
    sessions = (
        StudySession.objects.filter(is_active=True, end_time__gte=now)
        .select_related("host", "location")
        .order_by("start_time")
    )
    can_post = request.user.is_authenticated
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

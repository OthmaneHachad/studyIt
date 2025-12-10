from django.urls import path
from . import views

app_name = "study_sessions"

urlpatterns = [
    path("", views.session_list, name="session_list"),
    path("new/", views.session_create, name="session_create"),
    path("<int:session_id>/join/", views.request_session_join, name="join_session"),
    path("<int:session_id>/requests/", views.manage_session_requests, name="manage_requests"),
    path("requests/<int:enrollment_id>/<str:action>/", views.update_request_status, name="update_request"),
]


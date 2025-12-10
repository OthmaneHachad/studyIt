from django.urls import path
from . import views

app_name = "study_sessions"

urlpatterns = [
    path("", views.session_list, name="session_list"),
    path("new/", views.session_create, name="session_create"),
]


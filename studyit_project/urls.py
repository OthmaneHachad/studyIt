"""
URL configuration for studyit_project project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    # App URLs will be included here as they're developed
    # path("accounts/", include("accounts.urls")),
    # path("locations/", include("locations.urls")),
    # path("sessions/", include("study_sessions.urls")),
    # path("chat/", include("chat.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

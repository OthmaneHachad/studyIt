from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('requests/', views.chat_request_list, name='request_list'),
    path('requests/send/<int:recipient_id>/', views.send_chat_request, name='send_request'),
    path('requests/accept/<int:request_id>/', views.accept_chat_request, name='accept_request'),
    path('requests/reject/<int:request_id>/', views.reject_chat_request, name='reject_request'),
    path('requests/cancel/<int:request_id>/', views.cancel_chat_request, name='cancel_request'),
    path('requests/check/<int:recipient_id>/', views.check_pending_request, name='check_pending'),
    path('rooms/', views.chat_room_list, name='room_list'),
    path('rooms/<str:room_name>/', views.chat_room_detail, name='room_detail'),
    path('rooms/<str:room_name>/send/', views.send_message, name='send_message'),
    path('rooms/<str:room_name>/messages/', views.get_new_messages, name='get_messages'),
    # Call-related URLs
    path('calls/initiate/<str:room_name>/', views.initiate_call, name='initiate_call'),
    path('calls/<int:call_id>/accept/', views.accept_call, name='accept_call'),
    path('calls/<int:call_id>/reject/', views.reject_call, name='reject_call'),
    path('calls/<int:call_id>/cancel/', views.cancel_call, name='cancel_call'),
    path('calls/<int:call_id>/end/', views.end_call, name='end_call'),
    path('calls/<int:call_id>/status/', views.get_call_status, name='call_status'),
    path('calls/history/', views.call_history, name='call_history'),
]


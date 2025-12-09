"""
WebSocket URL routing for chat app
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/call/(?P<room_name>[^/]+)/$', consumers.CallSignalingConsumer.as_asgi()),
]


from django.contrib import admin
from .models import ChatRequest, ChatRoom, Message

@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__name', 'recipient__name', 'message']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['room_name', 'participant1', 'participant2', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['room_name', 'participant1__name', 'participant2__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'content_preview', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp', 'room']
    search_fields = ['content', 'sender__name', 'room__room_name']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

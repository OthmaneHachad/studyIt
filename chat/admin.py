from django.contrib import admin
from .models import ChatRequest, ChatRoom, Message, Call

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

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['caller', 'receiver', 'call_type', 'status', 'initiated_at', 'duration_display']
    list_filter = ['call_type', 'status', 'initiated_at']
    search_fields = ['caller__name', 'receiver__name']
    readonly_fields = ['initiated_at', 'accepted_at', 'ended_at', 'duration_seconds']
    
    def duration_display(self, obj):
        return obj.get_duration_display()
    duration_display.short_description = 'Duration'

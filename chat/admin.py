from django.contrib import admin
from .models import ChatRequest

@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__name', 'recipient__name', 'message']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['sender', 'recipient', 'message', 'status', 'created_at', 'updated_at']

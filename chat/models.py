from django.db import models
from django.contrib.auth.models import User
from accounts.models import StudentProfile
import uuid

class ChatRequest(models.Model):
    """Model for chat requests between students"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    sender = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='sent_chat_requests'
    )
    recipient = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='received_chat_requests'
    )
    message = models.TextField(
        max_length=500,
        help_text="Brief description of the problem or reason for the chat request"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Only allow one pending request between two users
        constraints = [
            models.UniqueConstraint(
                fields=['sender', 'recipient'],
                condition=models.Q(status='pending'),
                name='unique_pending_request'
            )
        ]
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['sender', 'status']),
        ]
    
    def __str__(self):
        return f"Chat request from {self.sender.name} to {self.recipient.name} - {self.get_status_display()}"
    
    def can_be_accepted(self):
        """Check if request can be accepted (must be pending)"""
        return self.status == 'pending'
    
    def can_be_cancelled(self):
        """Check if request can be cancelled (must be pending)"""
        return self.status == 'pending'

class ChatRoom(models.Model):
    """Model for DM chat rooms between two students"""
    room_name = models.CharField(max_length=100, unique=True, db_index=True)
    participant1 = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_participant1'
    )
    participant2 = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_participant2'
    )
    chat_request = models.OneToOneField(
        ChatRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_room',
        help_text="The chat request that created this room"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = [['participant1', 'participant2']]
        indexes = [
            models.Index(fields=['participant1', 'is_active']),
            models.Index(fields=['participant2', 'is_active']),
        ]
    
    def __str__(self):
        return f"Chat: {self.participant1.name} & {self.participant2.name}"
    
    @staticmethod
    def generate_room_name(user1_id, user2_id):
        """Generate a unique room name from two user IDs"""
        # Sort IDs to ensure consistent room name regardless of order
        ids = sorted([user1_id, user2_id])
        return f"dm_{ids[0]}_{ids[1]}"
    
    def get_other_participant(self, user_profile):
        """Get the other participant in the chat"""
        if user_profile == self.participant1:
            return self.participant2
        return self.participant1
    
    def has_participant(self, user_profile):
        """Check if a user is a participant in this room"""
        return user_profile in [self.participant1, self.participant2]
    
    def get_unread_count(self, user_profile):
        """Get unread message count for a user"""
        return self.messages.filter(
            is_read=False
        ).exclude(sender=user_profile).count()

class Message(models.Model):
    """Model for chat messages"""
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField(max_length=2000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['sender', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.name} in {self.room.room_name}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

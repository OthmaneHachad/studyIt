from django.db import models
from accounts.models import StudentProfile

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

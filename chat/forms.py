from django import forms
from .models import ChatRequest

class ChatRequestForm(forms.ModelForm):
    """Form for sending a chat request"""
    message = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Briefly describe the problem or reason for the chat request...',
            'rows': 4,
            'style': 'resize: vertical;'
        }),
        help_text="Briefly describe the problem or what you'd like to discuss (max 500 characters)",
        label="Message"
    )
    
    class Meta:
        model = ChatRequest
        fields = ['message']
    
    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        self.recipient = kwargs.pop('recipient', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that sender and recipient are provided
        if not self.sender or not self.recipient:
            raise forms.ValidationError("Sender and recipient are required.")
        
        # Check if sender is trying to send to themselves
        if self.sender == self.recipient:
            raise forms.ValidationError("You cannot send a chat request to yourself.")
        
        # Check if there's already a pending request between these users
        existing_request = ChatRequest.objects.filter(
            sender=self.sender,
            recipient=self.recipient,
            status='pending'
        ).first()
        
        if existing_request:
            raise forms.ValidationError(
                "You already have a pending chat request with this student. "
                "Please wait for them to respond or cancel your previous request."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        chat_request = super().save(commit=False)
        chat_request.sender = self.sender
        chat_request.recipient = self.recipient
        if commit:
            chat_request.save()
        return chat_request


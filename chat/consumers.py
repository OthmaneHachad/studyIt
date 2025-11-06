"""
WebSocket consumers for real-time chat
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from accounts.models import StudentProfile
from .models import ChatRoom, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat messages
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        
        # Verify user is authenticated and has access to this room
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has access to this room
        has_access = await self.check_room_access()
        if not has_access:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Leave room group"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get('message', '').strip()
            
            if not message_content:
                return
            
            # Get user profile
            user_profile = await self.get_user_profile()
            if not user_profile:
                await self.send(text_data=json.dumps({
                    'error': 'User profile not found'
                }))
                return
            
            # Get chat room
            chat_room = await self.get_chat_room()
            if not chat_room:
                await self.send(text_data=json.dumps({
                    'error': 'Chat room not found'
                }))
                return
            
            # Save message to database
            message = await self.save_message(chat_room, user_profile, message_content)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'username': self.user.username,
                    'sender_name': user_profile.name,
                    'sender_id': user_profile.id,
                    'timestamp': message.timestamp.isoformat() if message else None,
                    'message_id': message.id if message else None,
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def chat_message(self, event):
        """Receive message from room group"""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'sender_name': event.get('sender_name', ''),
            'sender_id': event.get('sender_id', ''),
            'timestamp': event.get('timestamp', ''),
            'message_id': event.get('message_id', ''),
        }))
    
    @database_sync_to_async
    def check_room_access(self):
        """Check if user has access to this room"""
        try:
            user_profile = StudentProfile.objects.get(user=self.user)
            chat_room = ChatRoom.objects.get(room_name=self.room_name, is_active=True)
            return chat_room.has_participant(user_profile)
        except (StudentProfile.DoesNotExist, ChatRoom.DoesNotExist):
            return False
    
    @database_sync_to_async
    def get_user_profile(self):
        """Get user's student profile"""
        try:
            return StudentProfile.objects.get(user=self.user)
        except StudentProfile.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_chat_room(self):
        """Get chat room"""
        try:
            return ChatRoom.objects.get(room_name=self.room_name, is_active=True)
        except ChatRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, chat_room, sender, content):
        """Save message to database"""
        message = Message.objects.create(
            room=chat_room,
            sender=sender,
            content=content
        )
        # Update room's updated_at timestamp
        chat_room.save()
        return message


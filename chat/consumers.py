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


class CallSignalingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling WebRTC signaling for voice/video calls
    """
    
    async def connect(self):
        """Accept WebSocket connection for call signaling"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.call_group_name = f'call_{self.room_name}'
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

        # Join call signaling group
        await self.channel_layer.group_add(
            self.call_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Notify user is ready for calls
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to call signaling server'
        }))

    async def disconnect(self, close_code):
        """Leave call signaling group"""
        # Notify other user if in active call
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'user_disconnected',
                'username': self.user.username,
            }
        )
        
        await self.channel_layer.group_discard(
            self.call_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive signaling messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Get user profile
            user_profile = await self.get_user_profile()
            if not user_profile:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'User profile not found'
                }))
                return
            
            # Handle different message types
            if message_type == 'call_offer':
                # Initiating a call - send WebRTC offer
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'call_offer',
                        'offer': data.get('offer'),
                        'call_type': data.get('call_type', 'video'),
                        'caller_id': user_profile.id,
                        'caller_name': user_profile.name,
                        'username': self.user.username,
                    }
                )
            
            elif message_type == 'call_answer':
                # Answering a call - send WebRTC answer
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'call_answer',
                        'answer': data.get('answer'),
                        'answerer_id': user_profile.id,
                        'answerer_name': user_profile.name,
                        'username': self.user.username,
                    }
                )
            
            elif message_type == 'ice_candidate':
                # Exchange ICE candidates for NAT traversal
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'ice_candidate',
                        'candidate': data.get('candidate'),
                        'sender_id': user_profile.id,
                        'username': self.user.username,
                    }
                )
            
            elif message_type == 'call_reject':
                # Rejecting a call
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'call_rejected',
                        'rejector_id': user_profile.id,
                        'rejector_name': user_profile.name,
                        'username': self.user.username,
                    }
                )
            
            elif message_type == 'call_end':
                # Ending a call
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'call_ended',
                        'ender_id': user_profile.id,
                        'ender_name': user_profile.name,
                        'username': self.user.username,
                    }
                )
            
            elif message_type == 'request_to_join':
                # User wants to join an active call
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'call_join_request',
                        'joiner_id': user_profile.id,
                        'joiner_name': user_profile.name,
                        'username': self.user.username,
                    }
                )
            
            elif message_type == 'call_cancel':
                # Cancelling a call before it's answered
                await self.channel_layer.group_send(
                    self.call_group_name,
                    {
                        'type': 'call_cancelled',
                        'canceller_id': user_profile.id,
                        'canceller_name': user_profile.name,
                        'username': self.user.username,
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    # Handler methods for group messages
    async def call_offer(self, event):
        """Forward call offer to other participant"""
        # Don't send to self
        user_profile = await self.get_user_profile()
        if user_profile and user_profile.id != event.get('caller_id'):
            await self.send(text_data=json.dumps({
                'type': 'call_offer',
                'offer': event.get('offer'),
                'call_type': event.get('call_type'),
                'caller_id': event.get('caller_id'),
                'caller_name': event.get('caller_name'),
            }))

    async def call_answer(self, event):
        """Forward call answer to caller"""
        user_profile = await self.get_user_profile()
        if user_profile and user_profile.id != event.get('answerer_id'):
            await self.send(text_data=json.dumps({
                'type': 'call_answer',
                'answer': event.get('answer'),
                'answerer_id': event.get('answerer_id'),
                'answerer_name': event.get('answerer_name'),
            }))

    async def ice_candidate(self, event):
        """Forward ICE candidate to other participant"""
        user_profile = await self.get_user_profile()
        if user_profile and user_profile.id != event.get('sender_id'):
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event.get('candidate'),
            }))

    async def call_rejected(self, event):
        """Forward call rejection to caller"""
        user_profile = await self.get_user_profile()
        if user_profile and user_profile.id != event.get('rejector_id'):
            await self.send(text_data=json.dumps({
                'type': 'call_rejected',
                'rejector_name': event.get('rejector_name'),
            }))

    async def call_ended(self, event):
        """Forward call end to other participant"""
        user_profile = await self.get_user_profile()
        if user_profile and user_profile.id != event.get('ender_id'):
            await self.send(text_data=json.dumps({
                'type': 'call_ended',
                'ender_name': event.get('ender_name'),
            }))

    async def call_cancelled(self, event):
        """Forward call cancellation to receiver"""
        user_profile = await self.get_user_profile()
        if user_profile and user_profile.id != event.get('canceller_id'):
            await self.send(text_data=json.dumps({
                'type': 'call_cancelled',
                'canceller_name': event.get('canceller_name'),
            }))

    async def call_join_request(self, event):
        """Forward join request to other participants"""
        # Don't send to the person who requested to join
        if self.user.username != event['username']:
            await self.send(text_data=json.dumps({
                'type': 'call_join_request',
                'joiner_id': event['joiner_id'],
                'joiner_name': event['joiner_name'],
            }))

    async def user_disconnected(self, event):
        """Notify when other user disconnects"""
        if event.get('username') != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_disconnected',
                'message': 'Other user disconnected'
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

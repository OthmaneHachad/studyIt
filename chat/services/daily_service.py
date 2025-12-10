"""
Daily.co Video API Integration Service

This module provides functions to interact with the Daily.co REST API
for creating and managing video call rooms.
"""

import requests
from django.conf import settings


class DailyAPIError(Exception):
    """Exception raised for Daily.co API errors"""
    pass


def create_room(room_name):
    """
    Create a Daily.co room for video calls.
    
    Args:
        room_name: Unique name for the room
        
    Returns:
        dict: Room information including:
            - name: Room name
            - url: Join URL for the room
            - id: Daily.co room ID
            
    Raises:
        DailyAPIError: If room creation fails
    """
    api_key = settings.DAILY_API_KEY
    if not api_key:
        raise DailyAPIError("DAILY_API_KEY not configured in settings")
    
    url = f"{settings.DAILY_API_BASE_URL}/rooms"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": room_name,
        "privacy": "private",  # Room is private, requires link to join
        "properties": {
            "enable_screenshare": True,
            "enable_chat": True,
            "start_video_off": False,
            "start_audio_off": False,
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        room_data = response.json()
        
        return {
            "name": room_data["name"],
            "url": room_data["url"],
            "id": room_data["id"]
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            # Room already exists, get it instead
            return get_room(room_name)
        raise DailyAPIError(f"Failed to create room: {e}")
    except requests.exceptions.RequestException as e:
        raise DailyAPIError(f"Network error: {e}")


def get_room(room_name):
    """
    Get information about an existing Daily.co room.
    
    Args:
        room_name: Name of the room to retrieve
        
    Returns:
        dict: Room information
        
    Raises:
        DailyAPIError: If room doesn't exist or retrieval fails
    """
    api_key = settings.DAILY_API_KEY
    if not api_key:
        raise DailyAPIError("DAILY_API_KEY not configured in settings")
    
    url = f"{settings.DAILY_API_BASE_URL}/rooms/{room_name}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        room_data = response.json()
        
        return {
            "name": room_data["name"],
            "url": room_data["url"],
            "id": room_data["id"]
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise DailyAPIError(f"Room '{room_name}' not found")
        raise DailyAPIError(f"Failed to get room: {e}")
    except requests.exceptions.RequestException as e:
        raise DailyAPIError(f"Network error: {e}")


def delete_room(room_name):
    """
    Delete a Daily.co room.
    
    Args:
        room_name: Name of the room to delete
        
    Returns:
        bool: True if deletion successful
        
    Raises:
        DailyAPIError: If deletion fails
    """
    api_key = settings.DAILY_API_KEY
    if not api_key:
        raise DailyAPIError("DAILY_API_KEY not configured in settings")
    
    url = f"{settings.DAILY_API_BASE_URL}/rooms/{room_name}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # Room already deleted or doesn't exist
            return True
        raise DailyAPIError(f"Failed to delete room: {e}")
    except requests.exceptions.RequestException as e:
        raise DailyAPIError(f"Network error: {e}")

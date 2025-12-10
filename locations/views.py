import json
import urllib.request
import urllib.parse
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from .models import Location


@login_required
@require_POST
def update_gps_location(request):
    """
    Update the current user's GPS location from browser geolocation.
    Expects JSON body with latitude and longitude.
    """
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
        
        # Validate coordinates
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid coordinate values'}, status=400)
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return JsonResponse({'error': 'Coordinates out of valid range'}, status=400)
        
        # Get or check for student profile
        try:
            profile = request.user.student_profile
        except:
            return JsonResponse({'error': 'Student profile not found'}, status=400)
        
        # Update GPS coordinates
        profile.current_latitude = latitude
        profile.current_longitude = longitude
        profile.location_updated_at = timezone.now()
        
        # Try to find nearest known location
        nearest_location = find_nearest_location(latitude, longitude)
        if nearest_location and nearest_location.get('auto_select', False):
            # Only auto-select if within 500m
            profile.current_location = nearest_location['location']
        
        profile.save()
        
        # Reverse geocode to get address (optional, may fail due to network)
        address_info = reverse_geocode(latitude, longitude)
        
        response_data = {
            'success': True,
            'message': 'Location updated successfully',
            'latitude': latitude,
            'longitude': longitude,
            'address': address_info,
            'location_updated_at': profile.location_updated_at.isoformat(),
        }
        
        if nearest_location:
            response_data['nearest_location'] = {
                'id': nearest_location['location'].id,
                'name': nearest_location['location'].name,
                'distance': Location.format_distance(nearest_location['distance']),
                'distance_meters': nearest_location['distance'],
                'auto_selected': nearest_location.get('auto_select', False),
            }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def reverse_geocode_view(request):
    """
    Reverse geocode coordinates to get address using OpenStreetMap Nominatim.
    """
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lon')
    
    if not latitude or not longitude:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinate values'}, status=400)
    
    address_info = reverse_geocode(latitude, longitude)
    
    if address_info:
        return JsonResponse({
            'success': True,
            'address': address_info,
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Could not geocode location',
        })


def reverse_geocode(latitude, longitude):
    """
    Use OpenStreetMap Nominatim API to reverse geocode coordinates.
    Returns address information or None on failure.
    """
    try:
        # Nominatim API endpoint
        base_url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': latitude,
            'lon': longitude,
            'zoom': 18,
            'addressdetails': 1,
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        # Create request with User-Agent header (required by Nominatim)
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'StudyIt/1.0 (Educational App)'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if 'error' in data:
                return None
            
            address = data.get('address', {})
            
            return {
                'display_name': data.get('display_name', ''),
                'building': address.get('building', address.get('amenity', '')),
                'road': address.get('road', ''),
                'neighbourhood': address.get('neighbourhood', address.get('suburb', '')),
                'city': address.get('city', address.get('town', address.get('village', ''))),
                'state': address.get('state', ''),
                'postcode': address.get('postcode', ''),
                'country': address.get('country', ''),
            }
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def find_nearest_location(latitude, longitude, max_distance_meters=None):
    """
    Find the nearest known location.
    If max_distance_meters is provided, only return locations within that distance.
    Returns dict with location, distance, and whether it's within auto-select range.
    """
    locations = Location.objects.filter(
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    nearest = None
    min_distance = float('inf')
    
    for location in locations:
        distance = location.distance_to(latitude, longitude)
        if distance is not None and distance < min_distance:
            min_distance = distance
            nearest = location
    
    if nearest:
        # Auto-select threshold is 500m, but always return the nearest
        auto_select = min_distance <= 500 if max_distance_meters is None else min_distance <= max_distance_meters
        return {
            'location': nearest,
            'distance': min_distance,
            'auto_select': auto_select,
        }
    
    return None


@login_required
@require_GET
def nearby_locations(request):
    """
    Get all locations sorted by distance from current coordinates.
    """
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lon')
    
    if not latitude or not longitude:
        # Try to use user's stored coordinates
        try:
            profile = request.user.student_profile
            if profile.has_gps_coordinates():
                latitude = profile.current_latitude
                longitude = profile.current_longitude
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No coordinates provided and no stored location',
                })
        except:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found',
            })
    else:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid coordinate values'}, status=400)
    
    # Get all active locations with coordinates
    locations = Location.objects.filter(is_active=True)
    
    location_list = []
    for loc in locations:
        loc_data = {
            'id': loc.id,
            'name': loc.name,
            'building_name': loc.building_name,
            'has_coordinates': loc.has_coordinates(),
        }
        
        if loc.has_coordinates():
            distance = loc.distance_to(latitude, longitude)
            loc_data['distance_meters'] = distance
            loc_data['distance_formatted'] = Location.format_distance(distance)
            loc_data['latitude'] = loc.latitude
            loc_data['longitude'] = loc.longitude
        else:
            loc_data['distance_meters'] = None
            loc_data['distance_formatted'] = 'Unknown'
        
        location_list.append(loc_data)
    
    # Sort by distance (locations without coordinates go last)
    location_list.sort(key=lambda x: x['distance_meters'] if x['distance_meters'] is not None else float('inf'))
    
    return JsonResponse({
        'success': True,
        'user_coordinates': {
            'latitude': latitude,
            'longitude': longitude,
        },
        'locations': location_list,
    })


@login_required
@require_GET
def nearby_classmates_api(request):
    """
    API endpoint to get classmates sorted by distance with coordinates.
    """
    try:
        profile = request.user.student_profile
    except:
        return JsonResponse({'error': 'Student profile not found'}, status=400)
    
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lon')
    
    if latitude and longitude:
        try:
            user_lat = float(latitude)
            user_lon = float(longitude)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid coordinate values'}, status=400)
    elif profile.has_gps_coordinates():
        user_lat = profile.current_latitude
        user_lon = profile.current_longitude
    else:
        return JsonResponse({
            'success': False,
            'error': 'No coordinates available',
        })
    
    # Get user's classes
    user_class_ids = set(profile.classes.values_list('id', flat=True))
    
    if not user_class_ids:
        return JsonResponse({
            'success': True,
            'message': 'No classes enrolled',
            'classmates': [],
        })
    
    # Import here to avoid circular imports
    from accounts.models import StudentProfile
    
    # Find classmates with GPS coordinates
    classmates = StudentProfile.objects.filter(
        is_active=True,
        classes__id__in=user_class_ids,
        current_latitude__isnull=False,
        current_longitude__isnull=False,
    ).exclude(id=profile.id).select_related('user', 'current_location').prefetch_related('classes').distinct()
    
    classmate_list = []
    for classmate in classmates:
        # Check if viewer can see this classmate's location
        if not classmate.can_view_location(profile):
            continue
        
        distance = classmate.distance_to(user_lat, user_lon)
        shared_classes = profile.get_shared_classes(classmate)
        
        classmate_list.append({
            'id': classmate.id,
            'user_id': classmate.user.id,
            'name': classmate.name,
            'year': classmate.get_year_display(),
            'distance_meters': distance,
            'distance_formatted': StudentProfile.format_distance(distance),
            'shared_classes': shared_classes,
            'location_name': classmate.current_location.name if classmate.current_location else None,
            'latitude': classmate.current_latitude,
            'longitude': classmate.current_longitude,
        })
    
    # Sort by distance
    classmate_list.sort(key=lambda x: x['distance_meters'] if x['distance_meters'] is not None else float('inf'))
    
    return JsonResponse({
        'success': True,
        'user_coordinates': {
            'latitude': user_lat,
            'longitude': user_lon,
        },
        'classmates': classmate_list,
        'total_count': len(classmate_list),
    })


@login_required
@require_POST  
def set_location_from_selection(request):
    """
    Set user's location from a selected known location.
    Also updates GPS coordinates if the location has them.
    """
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id')
        
        if not location_id:
            return JsonResponse({'error': 'Location ID is required'}, status=400)
        
        try:
            location = Location.objects.get(id=location_id, is_active=True)
        except Location.DoesNotExist:
            return JsonResponse({'error': 'Location not found'}, status=404)
        
        try:
            profile = request.user.student_profile
        except:
            return JsonResponse({'error': 'Student profile not found'}, status=400)
        
        # Update location
        profile.current_location = location
        
        # If location has coordinates, update GPS coordinates too
        if location.has_coordinates():
            profile.current_latitude = location.latitude
            profile.current_longitude = location.longitude
            profile.location_updated_at = timezone.now()
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Location set to {location.name}',
            'location': {
                'id': location.id,
                'name': location.name,
                'has_coordinates': location.has_coordinates(),
            },
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.db import models
from math import radians, cos, sin, asin, sqrt

class Location(models.Model):
    """Model for campus locations where students can study"""
    name = models.CharField(max_length=200, unique=True)
    building_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    # GPS coordinates
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude coordinate")
    address = models.CharField(max_length=500, blank=True, help_text="Full address from geocoding")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def has_coordinates(self):
        """Check if this location has GPS coordinates"""
        return self.latitude is not None and self.longitude is not None
    
    def distance_to(self, lat, lon):
        """
        Calculate distance in meters to a given point using Haversine formula
        Returns None if this location doesn't have coordinates
        """
        if not self.has_coordinates():
            return None
        
        # Haversine formula
        R = 6371000  # Earth's radius in meters
        
        lat1 = radians(self.latitude)
        lat2 = radians(lat)
        dlat = radians(lat - self.latitude)
        dlon = radians(lon - self.longitude)
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def distance_to_location(self, other_location):
        """Calculate distance to another Location object"""
        if not other_location or not other_location.has_coordinates():
            return None
        return self.distance_to(other_location.latitude, other_location.longitude)
    
    @staticmethod
    def format_distance(meters):
        """Format distance in human-readable format"""
        if meters is None:
            return "Unknown"
        if meters < 100:
            return f"{int(meters)} m"
        elif meters < 1000:
            return f"{int(meters)} m"
        else:
            km = meters / 1000
            return f"{km:.1f} km"

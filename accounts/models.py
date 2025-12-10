from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from math import radians, cos, sin, asin, sqrt

class Class(models.Model):
    """Model for academic classes/courses"""
    code = models.CharField(max_length=20, unique=True, help_text="e.g., CS2340")
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_classes', help_text="User who created this class (null if admin-created)")
    is_official = models.BooleanField(default=False, help_text="True if created by admin, False if user-created")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentClass(models.Model):
    """Through model for StudentProfile-Class relationship with expertise level"""
    EXPERTISE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='student_classes')
    course = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='student_enrollments')
    expertise_level = models.CharField(max_length=20, choices=EXPERTISE_CHOICES, default='beginner')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['course__code']
    
    def __str__(self):
        return f"{self.student.name} - {self.course.code} ({self.get_expertise_level_display()})"

class StudentProfile(models.Model):
    """Profile model for Student users"""
    YEAR_CHOICES = [
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('graduate', 'Graduate'),
    ]
    
    LOCATION_PRIVACY_CHOICES = [
        ('public', 'Show to Everyone'),
        ('classmates', 'Show to Classmates Only'),
        ('hidden', 'Hide from Everyone'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=200, help_text="Your full name")
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    classes = models.ManyToManyField(Class, through='StudentClass', related_name='students', blank=True)
    location_privacy = models.CharField(
        max_length=20,
        choices=LOCATION_PRIVACY_CHOICES,
        default='public',
        help_text="Control who can see your current location"
    )
    current_location = models.ForeignKey('locations.Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    # GPS coordinates for precise location
    current_latitude = models.FloatField(null=True, blank=True, help_text="Current latitude coordinate")
    current_longitude = models.FloatField(null=True, blank=True, help_text="Current longitude coordinate")
    location_updated_at = models.DateTimeField(null=True, blank=True, help_text="When the GPS location was last updated")
    is_active = models.BooleanField(default=True, help_text="Currently using StudyIt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_year_display()}"
    
    def get_classes_display(self):
        """Return comma-separated list of class codes"""
        return ", ".join([sc.course.code for sc in self.student_classes.all()])
    
    def get_shared_classes(self, other_profile):
        """Get list of classes shared with another student profile"""
        if not other_profile:
            return []
        my_classes = set(self.classes.values_list('code', flat=True))
        their_classes = set(other_profile.classes.values_list('code', flat=True))
        return list(my_classes.intersection(their_classes))
    
    def can_view_location(self, viewer_profile):
        """
        Check if the viewer profile can see this profile's location
        
        Args:
            viewer_profile: StudentProfile of the viewer (can be None for anonymous)
        
        Returns:
            bool: True if location should be visible to viewer
        """
        # If location is public, everyone can see it
        if self.location_privacy == 'public':
            return True
        
        # If hidden, no one can see it
        if self.location_privacy == 'hidden':
            return False
        
        # If classmates only, check if viewer shares any classes
        if self.location_privacy == 'classmates':
            if not viewer_profile:
                return False
            shared_classes = self.get_shared_classes(viewer_profile)
            return len(shared_classes) > 0
        
        # Default to hidden for unknown privacy settings
        return False
    
    def get_location_privacy_display_icon(self):
        """Get icon for current privacy setting"""
        icons = {
            'public': '🌍',
            'classmates': '👥',
            'hidden': '🔒',
        }
        return icons.get(self.location_privacy, '🔒')
    
    def get_matching_score(self, other_profile):
        """Calculate matching score with another student profile"""
        if not other_profile:
            return 0
        
        score = 0
        
        # Shared classes (10 points each)
        shared_classes = self.get_shared_classes(other_profile)
        score += len(shared_classes) * 10
        
        # Same location (5 points) - only if location is visible
        if (self.current_location and other_profile.current_location and 
            self.current_location == other_profile.current_location and
            self.can_view_location(other_profile)):
            score += 5
        
        # Both available (3 points)
        if self.location_privacy == 'public' and other_profile.location_privacy == 'public':
            score += 3
        
        # Same year (2 points)
        if self.year == other_profile.year:
            score += 2
        
        return score
    
    @property
    def pending_request_count(self):
        """Get count of pending incoming chat requests"""
        return self.received_chat_requests.filter(status='pending').count()
    
    def has_gps_coordinates(self):
        """Check if this profile has GPS coordinates"""
        return self.current_latitude is not None and self.current_longitude is not None
    
    def distance_to(self, lat, lon):
        """
        Calculate distance in meters to a given point using Haversine formula
        Returns None if this profile doesn't have coordinates
        """
        if not self.has_gps_coordinates():
            return None
        
        # Haversine formula
        R = 6371000  # Earth's radius in meters
        
        lat1 = radians(self.current_latitude)
        lat2 = radians(lat)
        dlat = radians(lat - self.current_latitude)
        dlon = radians(lon - self.current_longitude)
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def distance_to_profile(self, other_profile):
        """Calculate distance to another StudentProfile"""
        if not other_profile or not other_profile.has_gps_coordinates():
            return None
        return self.distance_to(other_profile.current_latitude, other_profile.current_longitude)
    
    @staticmethod
    def format_distance(meters):
        """Format distance in human-readable format"""
        if meters is None:
            return "Unknown"
        if meters < 100:
            return f"{int(meters)} m away"
        elif meters < 1000:
            return f"{int(meters)} m away"
        else:
            km = meters / 1000
            return f"{km:.1f} km away"

class TAProfile(models.Model):
    """Profile model for TA/Session Host users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ta_profile')
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    classes_teaching = models.ManyToManyField(Class, related_name='tas', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - TA"

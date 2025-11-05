from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=200, help_text="Your full name")
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    classes = models.ManyToManyField(Class, through='StudentClass', related_name='students', blank=True)
    location_privacy = models.BooleanField(default=False, help_text="Hide your location from others")
    current_location = models.ForeignKey('locations.Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
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
    
    def get_matching_score(self, other_profile):
        """Calculate matching score with another student profile"""
        if not other_profile:
            return 0
        
        score = 0
        
        # Shared classes (10 points each)
        shared_classes = self.get_shared_classes(other_profile)
        score += len(shared_classes) * 10
        
        # Same location (5 points)
        if (self.current_location and other_profile.current_location and 
            self.current_location == other_profile.current_location):
            score += 5
        
        # Both available/not hiding location (3 points)
        if not self.location_privacy and not other_profile.location_privacy:
            score += 3
        
        # Same year (2 points)
        if self.year == other_profile.year:
            score += 2
        
        return score

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

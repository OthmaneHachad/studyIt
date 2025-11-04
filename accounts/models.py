from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Class(models.Model):
    """Model for academic classes/courses"""
    code = models.CharField(max_length=20, unique=True, help_text="e.g., CS2340")
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentProfile(models.Model):
    """Profile model for Student users"""
    YEAR_CHOICES = [
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('graduate', 'Graduate'),
    ]
    
    EXPERTISE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=200, help_text="Your full name")
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    classes = models.ManyToManyField(Class, related_name='students', blank=True)
    expertise_level = models.CharField(max_length=20, choices=EXPERTISE_CHOICES, default='beginner')
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
        return ", ".join([cls.code for cls in self.classes.all()])

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

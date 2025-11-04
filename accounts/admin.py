from django.contrib import admin
from .models import StudentProfile, TAProfile, Class, StudentClass

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'is_official', 'created_by']
    search_fields = ['code', 'name']
    list_filter = ['department', 'is_official']
    readonly_fields = ['created_at']

@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'expertise_level', 'added_at']
    list_filter = ['expertise_level', 'added_at']
    search_fields = ['student__name', 'course__code', 'course__name']
    readonly_fields = ['added_at']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'year', 'is_active', 'current_location']
    list_filter = ['year', 'is_active', 'location_privacy']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TAProfile)
class TAProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'department', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['classes_teaching']

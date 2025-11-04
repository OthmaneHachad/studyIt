from django.contrib import admin
from .models import StudentProfile, TAProfile, Class

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department']
    search_fields = ['code', 'name']
    list_filter = ['department']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'year', 'expertise_level', 'is_active', 'current_location']
    list_filter = ['year', 'expertise_level', 'is_active']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['classes']

@admin.register(TAProfile)
class TAProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'department', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['classes_teaching']

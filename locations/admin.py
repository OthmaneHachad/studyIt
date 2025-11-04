from django.contrib import admin
from .models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'building_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'building_name']

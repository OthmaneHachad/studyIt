from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    # GPS Location APIs
    path('api/update-gps/', views.update_gps_location, name='update_gps'),
    path('api/reverse-geocode/', views.reverse_geocode_view, name='reverse_geocode'),
    path('api/nearby-locations/', views.nearby_locations, name='nearby_locations'),
    path('api/nearby-classmates/', views.nearby_classmates_api, name='nearby_classmates_api'),
    path('api/set-location/', views.set_location_from_selection, name='set_location'),
]


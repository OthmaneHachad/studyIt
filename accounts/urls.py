from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('browse/', views.profile_list, name='profile_list'),
    path('profile/add-class/', views.add_class, name='add_class'),
    path('profile/search-classes/', views.search_classes, name='search_classes'),
    path('profile/remove-class/<int:class_id>/', views.remove_class, name='remove_class'),
    path('profile/update-expertise/<int:class_id>/', views.update_class_expertise, name='update_class_expertise'),
]


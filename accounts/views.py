from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from .forms import LoginForm, UserRegistrationForm, StudentProfileForm, StudentClassForm, ClassForm
from .models import StudentProfile, TAProfile, Class, StudentClass

@login_required
def nearby_classmates(request):
    """Show classmates who are active and at the same location, with counts per class"""
    # Ensure the user has a student profile
    try:
        current_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.info(request, 'Please create your profile first.')
        return redirect('accounts:create_profile')
    
    # Ensure current location is set
    current_location = current_profile.current_location
    if current_location is None:
        messages.info(request, 'Set your current location to see nearby classmates.')
        return render(request, 'accounts/nearby.html', {
            'current_profile': current_profile,
            'current_location': None,
            'user_classes': current_profile.classes.all().order_by('code'),
            'counts_by_class': {},
            'grouped_by_class': {},
        })
    
    # Prepare user classes
    user_classes_qs = current_profile.classes.all().order_by('code')
    user_class_codes = set(user_classes_qs.values_list('code', flat=True))
    
    # Candidates: active students at the same location, excluding self
    candidates = (
        StudentProfile.objects
        .filter(is_active=True, current_location=current_location)
        .exclude(id=current_profile.id)
        .select_related('user', 'current_location')
        .prefetch_related('classes')
    )
    
    # Group visible classmates by shared classes and compute counts
    from collections import defaultdict
    grouped_by_class = defaultdict(list)
    counts_by_class = defaultdict(int)
    
    for profile in candidates:
        # Respect location privacy relative to viewer
        if not profile.can_view_location(current_profile):
            continue
        
        # Determine shared class codes
        their_codes = set(profile.classes.values_list('code', flat=True))
        shared_codes = their_codes.intersection(user_class_codes)
        
        for code in shared_codes:
            counts_by_class[code] += 1
            grouped_by_class[code].append(profile)
    
    # Sort group members by name for consistent display
    for code in grouped_by_class:
        grouped_by_class[code].sort(key=lambda p: p.name.lower())
    
    # Convert defaultdicts to normal dicts for template context
    counts_by_class = dict(counts_by_class)
    grouped_by_class = dict(grouped_by_class)
    
    # Build class data list for simpler template rendering
    user_classes_data = []
    for cls in user_classes_qs:
        code = cls.code
        user_classes_data.append({
            'code': code,
            'name': cls.name,
            'count': counts_by_class.get(code, 0),
            'members': grouped_by_class.get(code, []),
        })
    
    # Calculate summary statistics
    total_nearby_classmates = sum(counts_by_class.values())
    classes_with_students = sum(1 for count in counts_by_class.values() if count > 0)
    
    # Get unique classmates (a student may be in multiple classes)
    unique_classmates = set()
    for members in grouped_by_class.values():
        for member in members:
            unique_classmates.add(member.id)
    unique_nearby_count = len(unique_classmates)
    
    return render(request, 'accounts/nearby.html', {
        'current_profile': current_profile,
        'current_location': current_location,
        'user_classes': user_classes_qs,
        'user_classes_data': user_classes_data,
        'counts_by_class': counts_by_class,
        'grouped_by_class': grouped_by_class,
        'total_nearby_classmates': total_nearby_classmates,
        'classes_with_students': classes_with_students,
        'unique_nearby_count': unique_nearby_count,
        'has_gps': current_profile.has_gps_coordinates(),
    })

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def signup_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            
            # Store user_type in session for profile creation
            user_type = form.cleaned_data.get('user_type')
            request.session['user_type'] = user_type
            
            # Redirect to profile creation based on user type
            if user_type == 'student':
                return redirect('accounts:create_profile')
            else:
                # Create a basic TA profile and send them to sessions
                full_name = f"{user.first_name} {user.last_name}".strip() or user.username
                TAProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'name': full_name,
                        'department': '',
                        'is_active': True,
                    }
                )
                messages.info(request, 'TA profile created. You can now post study sessions.')
                return redirect('study_sessions:session_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def create_profile(request):
    """Create student profile after registration"""
    # Check if user already has a profile
    if hasattr(request.user, 'student_profile'):
        messages.info(request, 'You already have a profile. You can edit it instead.')
        return redirect('accounts:profile_edit')
    
    # Only allow students to create student profiles
    user_type = request.session.get('user_type')
    if user_type != 'student':
        messages.error(request, 'This page is only for students.')
        return redirect('home')
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            messages.success(request, 'Profile created successfully! You can now add your classes.')
            return redirect('accounts:profile')
    else:
        form = StudentProfileForm()
    
    return render(request, 'accounts/profile_form.html', {
        'form': form,
        'title': 'Create Your Profile',
        'submit_text': 'Create Profile'
    })

@login_required
def profile_view(request):
    """View own profile"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.info(request, 'Please create your profile first.')
        return redirect('accounts:create_profile')
    
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def profile_edit(request):
    """Edit own profile"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.info(request, 'Please create your profile first.')
        return redirect('accounts:create_profile')
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = StudentProfileForm(instance=profile)
    
    # Get all classes for this student with expertise levels
    student_classes = StudentClass.objects.filter(student=profile).select_related('course')
    
    return render(request, 'accounts/profile_form.html', {
        'form': form,
        'title': 'Edit Your Profile',
        'submit_text': 'Update Profile',
        'profile': profile,
        'student_classes': student_classes
    })

@login_required
def search_classes(request):
    """Search for existing classes"""
    query = request.GET.get('q', '').strip().upper()
    
    if len(query) < 2:
        return JsonResponse({'classes': []})
    
    classes = Class.objects.filter(
        models.Q(code__icontains=query) | models.Q(name__icontains=query)
    ).order_by('code')[:20]  # Limit to 20 results
    
    results = [{
        'id': cls.id,
        'code': cls.code,
        'name': cls.name,
        'department': cls.department or '',
        'is_official': cls.is_official
    } for cls in classes]
    
    return JsonResponse({'classes': results})

@login_required
def add_class(request):
    """Add a class to student profile with expertise level"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=400)
    
    if request.method == 'POST':
        form = StudentClassForm(request.POST, student_profile=profile)
        if form.is_valid():
            student_class = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Class {student_class.course.code} added successfully!',
                'class_id': student_class.id,
                'course_code': student_class.course.code,
                'course_name': student_class.course.name,
                'expertise_level': student_class.get_expertise_level_display()
            })
        else:
            return JsonResponse({'error': form.errors}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_class(request, class_id):
    """Remove a class from student profile"""
    try:
        profile = request.user.student_profile
        student_class = get_object_or_404(StudentClass, id=class_id, student=profile)
        course_code = student_class.course.code
        student_class.delete()
        messages.success(request, f'Class {course_code} removed successfully!')
    except StudentClass.DoesNotExist:
        messages.error(request, 'Class not found.')
    
    return redirect('accounts:profile_edit')

@login_required
def update_class_expertise(request, class_id):
    """Update expertise level for a class"""
    try:
        profile = request.user.student_profile
        student_class = get_object_or_404(StudentClass, id=class_id, student=profile)
        
        if request.method == 'POST':
            expertise_level = request.POST.get('expertise_level')
            if expertise_level in dict(StudentClass.EXPERTISE_CHOICES):
                student_class.expertise_level = expertise_level
                student_class.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Expertise level updated for {student_class.course.code}',
                    'expertise_level': student_class.get_expertise_level_display()
                })
            else:
                return JsonResponse({'error': 'Invalid expertise level'}, status=400)
    except StudentClass.DoesNotExist:
        return JsonResponse({'error': 'Class not found'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def profile_detail(request, user_id):
    """View another user's profile"""
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile = user.student_profile
        # Only show if profile is active
        if not profile.is_active:
            messages.error(request, 'This profile is not available.')
            return redirect('accounts:profile_list')
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('accounts:profile_list')
    
    # Get current user's profile for privacy checks
    try:
        viewer_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        viewer_profile = None
    
    # Check if viewer can see location
    viewing_own = request.user == user
    can_see_location = viewing_own or profile.can_view_location(viewer_profile)
    
    return render(request, 'accounts/profile_detail.html', {
        'profile': profile,
        'viewing_own': viewing_own,
        'can_see_location': can_see_location,
        'viewer_profile': viewer_profile
    })

@login_required
def update_location_privacy(request):
    """AJAX endpoint to update location privacy setting"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=400)
    
    privacy_setting = request.POST.get('location_privacy')
    
    # Validate the privacy setting
    valid_settings = dict(StudentProfile.LOCATION_PRIVACY_CHOICES).keys()
    if privacy_setting not in valid_settings:
        return JsonResponse({'error': 'Invalid privacy setting'}, status=400)
    
    # Update the privacy setting
    profile.location_privacy = privacy_setting
    profile.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Privacy updated to: {profile.get_location_privacy_display()}',
        'privacy_setting': privacy_setting,
        'privacy_display': profile.get_location_privacy_display(),
        'privacy_icon': profile.get_location_privacy_display_icon(),
    })

@login_required
def profile_list(request):
    """Browse all student profiles with advanced filtering"""
    # Get current user's profile for matching logic
    try:
        current_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        current_profile = None
    
    # Base query - active profiles only
    profiles = StudentProfile.objects.filter(is_active=True).select_related('user', 'current_location').prefetch_related('student_classes__course')
    
    # Exclude current user from results
    if current_profile:
        profiles = profiles.exclude(id=current_profile.id)
    
    # Search by name
    search_query = request.GET.get('search', '').strip()
    if search_query:
        profiles = profiles.filter(name__icontains=search_query)
    
    # Filter by class (support multiple classes)
    class_filters = request.GET.getlist('class')
    if class_filters:
        for class_code in class_filters:
            profiles = profiles.filter(classes__code=class_code)
    
    # Filter by year
    year_filter = request.GET.get('year')
    if year_filter:
        profiles = profiles.filter(year=year_filter)
    
    # Filter by location
    location_filter = request.GET.get('location')
    if location_filter:
        try:
            profiles = profiles.filter(current_location_id=int(location_filter))
        except (ValueError, TypeError):
            pass
    
    # Filter by expertise level
    expertise_filter = request.GET.get('expertise')
    if expertise_filter:
        profiles = profiles.filter(student_classes__expertise_level=expertise_filter)
    
    # Filter by availability (only show students who have public location)
    available_only = request.GET.get('available') == 'true'
    if available_only:
        profiles = profiles.filter(location_privacy='public')
    
    # Remove duplicates from joins
    profiles = profiles.distinct()
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        profiles = profiles.order_by('name')
    elif sort_by == 'name_desc':
        profiles = profiles.order_by('-name')
    elif sort_by == 'year':
        profiles = profiles.order_by('year', 'name')
    elif sort_by == 'relevance' and current_profile:
        # For relevance, we'll calculate shared classes (done in template for now)
        # Could be optimized with annotation in the future
        profiles = profiles.order_by('-created_at')
    else:
        profiles = profiles.order_by('name')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(profiles, 15)  # Show 15 profiles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Pre-calculate shared classes and visibility for each profile on current page
    profiles_with_shared = []
    for profile in page_obj.object_list:
        if current_profile:
            profile.shared_classes_list = profile.get_shared_classes(current_profile)
            profile.can_see_location = profile.can_view_location(current_profile)
        else:
            profile.shared_classes_list = []
            profile.can_see_location = False
        profiles_with_shared.append(profile)
    
    # Get all available classes and locations for filter dropdowns
    from locations.models import Location
    all_classes = Class.objects.all().order_by('code')
    all_locations = Location.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'profiles': profiles_with_shared,
        'current_profile': current_profile,
        'all_classes': all_classes,
        'all_locations': all_locations,
        'year_choices': StudentProfile.YEAR_CHOICES,
        'expertise_choices': StudentClass.EXPERTISE_CHOICES,
        # Preserve filter values for form
        'search_query': search_query,
        'selected_classes': class_filters,
        'selected_year': year_filter,
        'selected_location': location_filter,
        'selected_expertise': expertise_filter,
        'available_only': available_only,
        'selected_sort': sort_by,
        'total_count': paginator.count,
    }
    
    return render(request, 'accounts/profile_list.html', context)

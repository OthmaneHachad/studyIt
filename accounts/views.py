from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from .forms import LoginForm, UserRegistrationForm, StudentProfileForm, StudentClassForm, ClassForm
from .models import StudentProfile, TAProfile, Class, StudentClass

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
                # TA profile creation can be implemented later
                return redirect('home')
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
    
    return render(request, 'accounts/profile_detail.html', {
        'profile': profile,
        'viewing_own': request.user == user
    })

@login_required
def profile_list(request):
    """Browse all student profiles"""
    profiles = StudentProfile.objects.filter(is_active=True).select_related('user', 'current_location')
    
    # Optional: Add filtering by class, year, etc.
    class_filter = request.GET.get('class')
    year_filter = request.GET.get('year')
    
    if class_filter:
        profiles = profiles.filter(classes__code=class_filter)
    if year_filter:
        profiles = profiles.filter(year=year_filter)
    
    return render(request, 'accounts/profile_list.html', {
        'profiles': profiles.distinct()
    })

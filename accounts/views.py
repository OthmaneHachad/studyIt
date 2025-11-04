from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, UserRegistrationForm, StudentProfileForm
from .models import StudentProfile, TAProfile

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
            form.save_m2m()  # Save many-to-many relationships (classes)
            
            messages.success(request, 'Profile created successfully!')
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
    
    return render(request, 'accounts/profile_form.html', {
        'form': form,
        'title': 'Edit Your Profile',
        'submit_text': 'Update Profile',
        'profile': profile
    })

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

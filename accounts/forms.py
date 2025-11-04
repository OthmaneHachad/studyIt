from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudentProfile, TAProfile, Class, StudentClass

class LoginForm(forms.Form):
    """Form for user login"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    user_type = forms.ChoiceField(
        choices=[('student', 'Student'), ('ta', 'TA/Session Host')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        required=True,
        label='Account Type'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

class ClassForm(forms.ModelForm):
    """Form for creating a new class"""
    class Meta:
        model = Class
        fields = ['code', 'name', 'department']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CS2340',
                'style': 'text-transform: uppercase;'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course name'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department (optional)'
            }),
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # Check if class already exists
            if Class.objects.filter(code=code).exists():
                if not self.instance.pk:  # Only check if creating new
                    raise forms.ValidationError(f"A class with code '{code}' already exists.")
        return code

class StudentClassForm(forms.ModelForm):
    """Form for adding a class with expertise level"""
    course_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., CS2340',
            'style': 'text-transform: uppercase;'
        }),
        help_text="Enter class code (e.g., CS2340)"
    )
    course_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Course name (optional)'
        })
    )
    selected_class_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = StudentClass
        fields = ['expertise_level']
        widgets = {
            'expertise_level': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.student_profile = kwargs.pop('student_profile', None)
        super().__init__(*args, **kwargs)
    
    def clean_course_code(self):
        code = self.cleaned_data.get('course_code')
        if code:
            return code.upper().strip()
        return code
    
    def save(self, commit=True):
        course_code = self.cleaned_data['course_code']
        course_name = self.cleaned_data.get('course_name', '')
        selected_class_id = self.cleaned_data.get('selected_class_id')
        
        # If a class ID was provided, use that class
        if selected_class_id:
            try:
                course = Class.objects.get(id=selected_class_id)
                # Verify the code matches (should always match)
                if course.code != course_code:
                    course = None
            except (Class.DoesNotExist, ValueError):
                course = None
        else:
            course = None
        
        # If no course selected, get or create the class
        if not course:
            course, created = Class.objects.get_or_create(
                code=course_code,
                defaults={
                    'name': course_name or course_code,
                    'created_by': self.student_profile.user if self.student_profile else None,
                    'is_official': False
                }
            )
        
        # Create or update StudentClass
        student_class, created = StudentClass.objects.get_or_create(
            student=self.student_profile,
            course=course,
            defaults={'expertise_level': self.cleaned_data['expertise_level']}
        )
        
        if not created:
            student_class.expertise_level = self.cleaned_data['expertise_level']
            student_class.save()
        
        return student_class

class StudentProfileForm(forms.ModelForm):
    """Form for creating/editing Student profile"""
    # Remove the old classes field - we'll handle classes separately
    
    class Meta:
        model = StudentProfile
        fields = ['name', 'year', 'location_privacy']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location_privacy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


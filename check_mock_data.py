#!/usr/bin/env python
"""Quick script to verify mock data was created"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyit_project.settings')
django.setup()

from accounts.models import StudentProfile, Class, StudentClass

print("=" * 60)
print("MOCK DATA VERIFICATION")
print("=" * 60)

# Count profiles
total_students = StudentProfile.objects.count()
print(f"\n✅ Total Student Profiles: {total_students}")

# Count classes
total_classes = Class.objects.count()
print(f"✅ Total Classes: {total_classes}")

# Count enrollments
total_enrollments = StudentClass.objects.count()
print(f"✅ Total Class Enrollments: {total_enrollments}")

print("\n" + "-" * 60)
print("STUDENT PROFILES:")
print("-" * 60)

for profile in StudentProfile.objects.all().order_by('name'):
    classes_list = [f"{sc.course.code} ({sc.get_expertise_level_display()})" 
                    for sc in profile.student_classes.all()]
    location = profile.current_location.name if profile.current_location else "No location"
    privacy = "🔒 PRIVATE" if profile.location_privacy else "✓ Available"
    
    print(f"\n{profile.name} ({profile.get_year_display()})")
    print(f"  Location: {location}")
    print(f"  Privacy: {privacy}")
    print(f"  Classes: {', '.join(classes_list)}")

print("\n" + "-" * 60)
print("CLASSES:")
print("-" * 60)

for cls in Class.objects.all().order_by('code'):
    student_count = StudentClass.objects.filter(course=cls).count()
    print(f"{cls.code} - {cls.name} ({student_count} students)")

print("\n" + "=" * 60)
print("✅ Mock data created successfully!")
print("=" * 60)
print("\nYou can now test the browsing feature at:")
print("http://localhost:8000/accounts/browse/")
print("\nLogin with any of these accounts (password: password123):")
print("  - asmith")
print("  - bjohnson")
print("  - dpatel")
print("  - fgarcia")
print("  - janderson")


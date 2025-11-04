# Generated manually to handle M2M through relationship

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # First, remove the old expertise_level field
        migrations.RemoveField(
            model_name='studentprofile',
            name='expertise_level',
        ),
        # Add new fields to Class
        migrations.AddField(
            model_name='class',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='class',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_classes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='class',
            name='is_official',
            field=models.BooleanField(default=False),
        ),
        # Create StudentClass model
        migrations.CreateModel(
            name='StudentClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expertise_level', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner', max_length=20)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_enrollments', to='accounts.class')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_classes', to='accounts.studentprofile')),
            ],
            options={
                'ordering': ['course__code'],
                'unique_together': {('student', 'course')},
            },
        ),
        # Remove old classes field
        migrations.RemoveField(
            model_name='studentprofile',
            name='classes',
        ),
        # Add new classes field with through relationship
        migrations.AddField(
            model_name='studentprofile',
            name='classes',
            field=models.ManyToManyField(blank=True, related_name='students', through='accounts.StudentClass', to='accounts.class'),
        ),
    ]

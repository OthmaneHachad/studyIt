# Generated manually for location_privacy field update

from django.db import migrations, models


def convert_boolean_to_choice(apps, schema_editor):
    """
    Convert existing boolean location_privacy values to new choice values:
    - False (public) -> 'public'
    - True (hidden) -> 'hidden'
    """
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    
    # Update all profiles with location_privacy=False to 'public'
    StudentProfile.objects.filter(location_privacy=False).update(location_privacy='public')
    
    # Update all profiles with location_privacy=True to 'hidden'
    StudentProfile.objects.filter(location_privacy=True).update(location_privacy='hidden')


def reverse_choice_to_boolean(apps, schema_editor):
    """
    Reverse migration: Convert choice values back to boolean:
    - 'public' or 'classmates' -> False
    - 'hidden' -> True
    """
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    
    # Convert 'public' and 'classmates' to False (visible)
    StudentProfile.objects.filter(location_privacy__in=['public', 'classmates']).update(location_privacy=False)
    
    # Convert 'hidden' to True
    StudentProfile.objects.filter(location_privacy='hidden').update(location_privacy=True)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_mock_students'),
    ]

    operations = [
        # Step 1: Change the field type to CharField (Django will preserve data as '0'/'1')
        migrations.AlterField(
            model_name='studentprofile',
            name='location_privacy',
            field=models.CharField(
                max_length=20,
                default='public',
            ),
        ),
        
        # Step 2: Convert boolean values ('True'/'False' or 1/0) to choice strings
        migrations.RunSQL(
            sql=[
                # Convert False/0 to 'public'
                "UPDATE accounts_studentprofile SET location_privacy = 'public' WHERE location_privacy IN ('0', 'False', 'false', '');",
                # Convert True/1 to 'hidden'
                "UPDATE accounts_studentprofile SET location_privacy = 'hidden' WHERE location_privacy IN ('1', 'True', 'true');",
            ],
            reverse_sql=[
                # Reverse: Convert 'public' and 'classmates' to False/0
                "UPDATE accounts_studentprofile SET location_privacy = '0' WHERE location_privacy IN ('public', 'classmates');",
                # Convert 'hidden' to True/1
                "UPDATE accounts_studentprofile SET location_privacy = '1' WHERE location_privacy = 'hidden';",
            ],
        ),
        
        # Step 3: Add the choices constraint
        migrations.AlterField(
            model_name='studentprofile',
            name='location_privacy',
            field=models.CharField(
                choices=[
                    ('public', 'Show to Everyone'),
                    ('classmates', 'Show to Classmates Only'),
                    ('hidden', 'Hide from Everyone'),
                ],
                default='public',
                help_text='Control who can see your current location',
                max_length=20,
            ),
        ),
    ]


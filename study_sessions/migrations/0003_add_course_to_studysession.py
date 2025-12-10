from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_studentprofile_current_latitude_and_more"),
        ("study_sessions", "0002_sessionenrollment"),
    ]

    operations = [
        migrations.AddField(
            model_name="studysession",
            name="course",
            field=models.ForeignKey(
                to="accounts.class",
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name="study_sessions",
                help_text="Optional: Label this session with a specific class/course",
            ),
        ),
    ]



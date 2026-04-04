from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0006_merge_activity_migrations"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="activitytype",
            name="category",
        ),
    ]

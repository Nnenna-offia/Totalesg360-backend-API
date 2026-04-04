from django.db import migrations


class Migration(migrations.Migration):

    # This is an auto-created merge migration to resolve multiple leaf nodes.
    dependencies = [
        ("activities", "0004_alter_activitytype_indicator"),
        ("activities", "0005_remove_activity_group"),
    ]

    operations = []

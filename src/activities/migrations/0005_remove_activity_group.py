from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0004_add_ui_fields_activitytype"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="activitytype",
            name="activity_group",
        ),
    ]

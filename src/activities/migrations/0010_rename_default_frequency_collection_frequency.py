from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0009_activitytype_default_frequency"),
    ]

    operations = [
        migrations.RenameField(
            model_name="activitytype",
            old_name="default_frequency",
            new_name="collection_frequency",
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0003_require_indicator"),
    ]

    operations = [
        migrations.AddField(
            model_name="activitytype",
            name="activity_group",
            field=models.CharField(default="General", max_length=255),
        ),
        migrations.AddField(
            model_name="activitytype",
            name="display_order",
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AddField(
            model_name="activitytype",
            name="data_type",
            field=models.CharField(default="number", max_length=20, db_index=True),
        ),
        migrations.AddField(
            model_name="activitytype",
            name="requires_evidence",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="activitytype",
            name="is_required",
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]

# Generated migration for adding indicator FK to ActivityType

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0001_initial'),
        ('indicators', '0003_remove_source_frameworks'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitytype',
            name='indicator',
            field=models.ForeignKey(
                blank=True,
                help_text='The indicator that this activity type contributes to',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='activity_types',
                to='indicators.indicator'
            ),
        ),
    ]

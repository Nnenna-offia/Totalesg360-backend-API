# Generated migration for adding collection_method to Indicator

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0003_remove_source_frameworks'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='collection_method',
            field=models.CharField(
                choices=[('activity', 'Activity Based'), ('direct', 'Direct Submission')],
                db_index=True,
                default='direct',
                help_text='Activity-based indicators are calculated from activities; direct indicators are manually submitted',
                max_length=20
            ),
        ),
    ]

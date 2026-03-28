# Migration to add department management features

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0007_alter_businessunit_options_and_more'),
    ]

    operations = [
        # Add head field to Department model
        migrations.AddField(
            model_name='department',
            name='head',
            field=models.ForeignKey(
                blank=True,
                help_text='Head of department (optional)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='departments_led',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Add index for Department organization
        migrations.AddIndex(
            model_name='department',
            index=models.Index(
                fields=['organization'],
                name='organizations_organiz_6b8afd_idx'
            ),
        ),
    ]

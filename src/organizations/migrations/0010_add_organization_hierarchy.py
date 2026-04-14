# Migration to add organization hierarchy support (parent, organization_type)
# Enables multi-level organization structures (Groups → Subsidiaries → Facilities)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0009_add_reporting_frequency'),
    ]

    operations = [
        # Add parent field (self-referencing FK for hierarchy)
        migrations.AddField(
            model_name='organization',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                help_text='Parent organization (for subsidiaries and business units)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subsidiaries',
                to='organizations.organization'
            ),
        ),
        
        # Add organization_type field
        migrations.AddField(
            model_name='organization',
            name='organization_type',
            field=models.CharField(
                choices=[
                    ('group', 'Group / Parent Company'),
                    ('subsidiary', 'Subsidiary / Business Unit'),
                    ('facility', 'Facility / Operating Site'),
                    ('department', 'Department / Division'),
                ],
                db_index=True,
                default='subsidiary',
                help_text='Organization type in hierarchy: Group, Subsidiary, Facility, Department',
                max_length=20
            ),
        ),
        
        # Add index for organization_type
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(
                fields=['organization_type'],
                name='organizations_organizatio_type_idx'
            ),
        ),
        
        # Add composite index for parent + organization_type lookups
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(
                fields=['parent', 'organization_type'],
                name='organizations_parent_type_idx'
            ),
        ),
    ]

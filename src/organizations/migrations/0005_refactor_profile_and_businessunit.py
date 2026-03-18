from django.db import migrations, models
import django.db.models.deletion
import uuid


def migrate_settings_to_profile(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    OrgSettings = apps.get_model('organizations', 'OrganizationSettings')
    OrgProfile = apps.get_model('organizations', 'OrganizationProfile')

    for s in OrgSettings.objects.all():
        org = s.organization
        # create profile and copy fields if present
        profile, created = OrgProfile.objects.get_or_create(organization=org)
        changed = False
        if hasattr(s, 'registered_business_name') and s.registered_business_name:
            profile.registered_business_name = s.registered_business_name
            changed = True
        if hasattr(s, 'cac_registration_number') and s.cac_registration_number:
            profile.cac_registration_number = s.cac_registration_number
            changed = True
        if hasattr(s, 'company_size') and s.company_size:
            profile.company_size = s.company_size
            changed = True
        if hasattr(s, 'operational_locations') and s.operational_locations:
            profile.operational_locations = s.operational_locations
            changed = True
        if hasattr(s, 'logo') and s.logo:
            # move reference to file path
            profile.logo = s.logo
            changed = True
        if changed:
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_organization_company_size_organization_logo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationProfile',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('registered_business_name', models.CharField(blank=True, max_length=500, null=True)),
                ('cac_registration_number', models.CharField(blank=True, max_length=100, null=True)),
                ('company_size', models.CharField(blank=True, max_length=20, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='organization_logos/')),
                ('operational_locations', models.JSONField(blank=True, default=list)),
                ('fiscal_year_start_month', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('fiscal_year_end_month', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('cac_document', models.FileField(blank=True, null=True, upload_to='organization_documents/')),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='organizations.organization')),
            ],
            options={
                'db_table': 'organizations_profile',
            },
        ),
        migrations.CreateModel(
            name='BusinessUnit',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_units', to='organizations.organization')),
            ],
            options={
                'db_table': 'organizations_businessunit',
            },
        ),
        migrations.AddField(
            model_name='organizationsettings',
            name='local_reporting_frequency',
            field=models.CharField(default='daily', max_length=20),
        ),
        migrations.AddField(
            model_name='organizationsettings',
            name='global_reporting_frequency',
            field=models.CharField(default='weekly', max_length=20),
        ),
        migrations.AddField(
            model_name='organizationsettings',
            name='auto_compliance_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrate_settings_to_profile, migrations.RunPython.noop),
        # Note: older migration states may not include the profile fields on OrganizationSettings.
        # We migrate values into OrganizationProfile above and avoid removing fields here to
        # prevent KeyError across different environments. Manual cleanup can be performed later.
    ]

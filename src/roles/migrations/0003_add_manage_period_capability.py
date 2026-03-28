from django.db import migrations


def forwards(apps, schema_editor):
    Capability = apps.get_model('roles', 'Capability')
    Role = apps.get_model('roles', 'Role')
    RoleCapability = apps.get_model('roles', 'RoleCapability')

    cap_code = 'manage_period'
    cap, created = Capability.objects.get_or_create(code=cap_code, defaults={'name': 'Manage Period', 'description': 'Create and manage reporting periods'})

    try:
        role = Role.objects.get(code='org_owner')
    except Role.DoesNotExist:
        role = None

    if role:
        # create role-capability mapping if not exists
        RoleCapability.objects.get_or_create(role=role, capability=cap)


def backwards(apps, schema_editor):
    Capability = apps.get_model('roles', 'Capability')
    Role = apps.get_model('roles', 'Role')
    RoleCapability = apps.get_model('roles', 'RoleCapability')

    cap_code = 'manage_period'
    try:
        cap = Capability.objects.get(code=cap_code)
    except Capability.DoesNotExist:
        return

    # remove mappings to org_owner role
    try:
        role = Role.objects.get(code='org_owner')
    except Role.DoesNotExist:
        role = None

    if role:
        RoleCapability.objects.filter(role=role, capability=cap).delete()

    # if no other role uses this capability, delete it
    if not RoleCapability.objects.filter(capability=cap).exists():
        cap.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0002_alter_capability_options_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

from django.core.management.base import BaseCommand
from roles.models import Capability


DEFAULT_CAPABILITIES = [
    # Organization
    ('org.manage', 'Manage Organization', 'Update org settings and configuration'),
    ('org.invite_members', 'Invite Members', 'Invite and manage organization members'),
    ('org.manage_facilities', 'Manage Facilities', 'Create/update organization facilities'),
    ('org.view_members', 'View Members', 'View organization membership list'),
    ('department.manage', 'Manage Departments', 'Create/update/delete organization departments'),

    # Activity
    ('activity_type.view', 'View Activity Types', 'View activity type catalog'),
    ('activity.submit', 'Submit Activity', 'Submit activity data for organization'),
    ('activity.edit', 'Edit Activity', 'Edit submitted activity data'),
    ('activity.delete', 'Delete Activity', 'Delete activity data'),
    ('activity.view_submissions', 'View Activity Submissions', 'View submissions for activity data'),

    # Emission
    ('emission.view', 'View Emissions', 'View emissions reports and dashboards'),
    ('emission.view_scope_breakdown', 'View Emission Scope Breakdown', 'View scope breakdown of emissions'),

    # Targets
    ('target.create', 'Create Target', 'Create sustainability targets'),
    ('target.edit', 'Edit Target', 'Edit sustainability targets'),
    ('target.delete', 'Delete Target', 'Delete sustainability targets'),
    ('target.view', 'View Targets', 'View sustainability targets'),

    # Indicators
    ('indicator.view', 'View Indicators', 'View system indicators'),
    ('compliance.view', 'View Compliance', 'View compliance and report completion'),

    # Platform admin (global)
    ('scope.manage', 'Manage Scopes', 'Platform scope management'),
    ('activity_type.manage', 'Manage Activity Types', 'Manage activity type catalog'),
    ('emission_factor.manage', 'Manage Emission Factors', 'Manage emission factors database'),
    ('indicator.manage', 'Manage Indicators', 'Manage system indicators'),
    ('framework.manage', 'Manage Frameworks', 'Manage frameworks and mappings'),

    # compatibility/system
    ('manage_roles', 'Manage Roles', 'Create/update/delete roles and assign capabilities'),
]


class Command(BaseCommand):
    help = 'Seed default capabilities into the database'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be created')

    def handle(self, *args, **options):
        dry = options.get('dry_run')
        created = []
        for code, name, desc in DEFAULT_CAPABILITIES:
            obj, was_created = Capability.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
            if was_created:
                created.append(code)
                if dry:
                    obj.delete()
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created capabilities: {", ".join(created)}'))
        else:
            self.stdout.write('No capabilities created; all exist already.')

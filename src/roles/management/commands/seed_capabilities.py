from django.core.management.base import BaseCommand
from roles.models import Capability


DEFAULT_CAPABILITIES = [
    ('manage_roles', 'Manage Roles', 'Create/update/delete roles and assign capabilities'),
    ('manage_indicators', 'Manage Indicators', 'Create/update/delete indicators'),
    ('submit_indicator', 'Submit Indicator', 'Submit indicator values'),
    ('manage_period', 'Manage Reporting Period', 'Create/finalize reporting periods'),
    ('approve_submission', 'Approve Submission', 'Approve submitted values'),
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

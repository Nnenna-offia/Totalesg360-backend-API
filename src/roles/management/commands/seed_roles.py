# roles/management/commands/seed_roles.py
from django.core.management.base import BaseCommand
from django.db import transaction
from roles.models import Role, Capability, RoleCapability
from roles.capabilities import Capabilities
from roles.role_capabilities import ROLE_CAPABILITIES


class Command(BaseCommand):
    help = 'Seed roles and capabilities for the ESG platform'

    def handle(self, *args, **options):
        self.stdout.write('Seeding capabilities...')
        self._seed_capabilities()
        
        self.stdout.write('Seeding roles...')
        self._seed_roles()
        
        self.stdout.write('Mapping roles to capabilities...')
        self._map_role_capabilities()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded roles and capabilities'))

    @transaction.atomic
    def _seed_capabilities(self):
        """Create Capability records from Capabilities class by introspecting the Capabilities constants."""
        created = 0
        for attr in dir(Capabilities):
            # pick uppercase attributes which we use as constants
            if not attr.isupper():
                continue
            code = getattr(Capabilities, attr)
            obj, was_created = Capability.objects.get_or_create(code=code, defaults={'name': code, 'description': ''})
            if was_created:
                created += 1

        self.stdout.write(f'  Created/verified capabilities (new created: {created})')

    @transaction.atomic
    def _seed_roles(self):
        """Create Role records."""
        roles_data = [
            {
                'code': 'org_owner',
                'name': 'Org Owner',
                'description': 'Organization owner with full organization-level permissions',
                'is_system': True,
            },
            {
                'code': 'sustainability_manager',
                'name': 'Sustainability Manager',
                'description': 'Manager for sustainability operations and targets',
                'is_system': True,
            },
            {
                'code': 'data_contributor',
                'name': 'Data Contributor',
                'description': 'Contributes activity and indicator data',
                'is_system': True,
            },
            {
                'code': 'viewer',
                'name': 'Viewer',
                'description': 'Read-only viewer role',
                'is_system': True,
            },
        ]
        
        for role_data in roles_data:
            Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_system': role_data['is_system'],
                }
            )
        
        self.stdout.write(f'  Created/verified {len(roles_data)} roles')

    @transaction.atomic
    def _map_role_capabilities(self):
        """Map roles to capabilities using ROLE_CAPABILITIES dict."""
        for role_code, capability_codes in ROLE_CAPABILITIES.items():
            try:
                role = Role.objects.get(code=role_code)
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Role {role_code} not found, skipping'))
                continue
            
            for cap_code in capability_codes:
                try:
                    capability = Capability.objects.get(code=cap_code)
                    RoleCapability.objects.get_or_create(
                        role=role,
                        capability=capability,
                    )
                except Capability.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  Capability {cap_code} not found, skipping'))
                    continue
            
            count = RoleCapability.objects.filter(role=role).count()
            self.stdout.write(f'  {role.name}: {count} capabilities')

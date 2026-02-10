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
        """Create Capability records from Capabilities class."""
        capabilities_data = [
            # Organization
            {
                'code': Capabilities.MANAGE_ORGANIZATION,
                'name': 'Manage Organization',
                'description': 'Can update organization settings, sector config',
                'pillar': '',
            },
            {
                'code': Capabilities.MANAGE_USERS,
                'name': 'Manage Users',
                'description': 'Can invite users, assign roles, manage memberships',
                'pillar': '',
            },
            # Configuration
            {
                'code': Capabilities.CONFIGURE_ESG,
                'name': 'Configure ESG Settings',
                'description': 'Can configure scopes, permits, frameworks',
                'pillar': '',
            },
            {
                'code': Capabilities.MANAGE_TARGETS,
                'name': 'Manage Targets',
                'description': 'Can create and edit ESG targets',
                'pillar': '',
            },
            # Data submission
            {
                'code': Capabilities.SUBMIT_ENVIRONMENTAL,
                'name': 'Submit Environmental Data',
                'description': 'Can submit emissions, energy, waste, water data',
                'pillar': 'Environmental',
            },
            {
                'code': Capabilities.SUBMIT_SOCIAL,
                'name': 'Submit Social Data',
                'description': 'Can submit workforce, training, HSE data',
                'pillar': 'Social',
            },
            {
                'code': Capabilities.SUBMIT_GOVERNANCE,
                'name': 'Submit Governance Data',
                'description': 'Can submit board, policy, compliance data',
                'pillar': 'Governance',
            },
            # Review
            {
                'code': Capabilities.VIEW_DASHBOARDS,
                'name': 'View Dashboards',
                'description': 'Can view ESG dashboards and reports',
                'pillar': '',
            },
            {
                'code': Capabilities.REVIEW_SUBMISSIONS,
                'name': 'Review Submissions',
                'description': 'Can review and approve data submissions',
                'pillar': '',
            },
        ]
        
        for cap_data in capabilities_data:
            Capability.objects.get_or_create(
                code=cap_data['code'],
                defaults={
                    'name': cap_data['name'],
                    'description': cap_data['description'],
                    'pillar': cap_data['pillar'],
                }
            )
        
        self.stdout.write(f'  Created/verified {len(capabilities_data)} capabilities')

    @transaction.atomic
    def _seed_roles(self):
        """Create Role records."""
        roles_data = [
            {
                'code': 'org_admin',
                'name': 'Organization Administrator',
                'description': 'Full control over organization settings, users, and data',
                'is_system': True,
            },
            {
                'code': 'environmental_officer',
                'name': 'Environmental Officer',
                'description': 'Submits and manages environmental data',
                'is_system': True,
            },
            {
                'code': 'social_officer',
                'name': 'Social Officer',
                'description': 'Submits and manages social data',
                'is_system': True,
            },
            {
                'code': 'governance_officer',
                'name': 'Governance Officer',
                'description': 'Submits and manages governance data',
                'is_system': True,
            },
            {
                'code': 'auditor',
                'name': 'Auditor / Reviewer',
                'description': 'Reviews submissions and provides oversight',
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

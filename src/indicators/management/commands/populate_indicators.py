"""Management command: Create Indicator entries and optionally FrameworkIndicator/OrganizationIndicator mappings.

Usage:
  ./manage.py populate_indicators --org-id 1 --count 20 --pillar "Environmental" --framework-id 1 --fixtures tmp/indicators.json
"""
import random
import json
from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from indicators.models import Indicator, FrameworkIndicator, OrganizationIndicator
from organizations.models import Organization, RegulatoryFramework


class Command(BaseCommand):
    help = 'Populate Indicators and optionally FrameworkIndicator/OrganizationIndicator mappings'

    def add_arguments(self, parser):
        parser.add_argument('--org-id', type=str, required=True, help='Organization ID (UUID or name substring match)')
        parser.add_argument('--count', type=int, default=10, help='Number of indicators to create')
        parser.add_argument('--pillar', type=str, default='Environmental', help='Pillar name or code (Environmental/Social/Governance)')
        parser.add_argument('--data-type', type=str, default='numeric', help='Data type for indicators')
        parser.add_argument('--unit', type=str, default='kg', help='Unit string for indicators')
        parser.add_argument('--framework-id', type=int, help='Framework ID to map indicators to')
        parser.add_argument('--framework-code', type=str, help='Framework code (GRI/SASB/TCFD)')
        parser.add_argument('--create-mappings', action='store_true', help='Create OrganizationIndicator/FrameworkIndicator mappings')
        parser.add_argument('--dry-run', action='store_true', help='Don\'t write to DB')
        parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
        parser.add_argument('--fixtures', type=str, help='Path to write Django JSON fixtures')

    def handle(self, *args, **options):
        if options['seed'] is not None:
            random.seed(options['seed'])

        try:
            # Try to get by UUID first, then by name substring
            org = None
            try:
                import uuid
                # Validate UUID format
                uuid.UUID(options['org_id'])
                org = Organization.objects.get(id=options['org_id'])
            except (ValueError, Organization.DoesNotExist):
                # If not a UUID or not found, try name match
                org = Organization.objects.filter(name__icontains=options['org_id']).first()
            
            if not org:
                raise Organization.DoesNotExist
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR('Organization not found.'))
            self.stdout.write('Available organizations:')
            for o in Organization.objects.values('id', 'name'):
                self.stdout.write(f"  {o['id']}: {o['name']}")
            raise CommandError('Please provide a valid organization ID or name')

        # Resolve pillar from choices
        pillar_code = None
        if options['pillar']:
            pillar_upper = options['pillar'].upper()
            # Map common names to codes
            pillar_map = {
                'ENV': 'ENV', 'ENVIRONMENTAL': 'ENV',
                'SOC': 'SOC', 'SOCIAL': 'SOC',
                'GOV': 'GOV', 'GOVERNANCE': 'GOV',
            }
            pillar_code = pillar_map.get(pillar_upper)
            if not pillar_code:
                self.stdout.write(self.style.WARNING(f"Pillar '{options['pillar']}' not recognized. Using ENV (Environmental)."))
                pillar_code = 'ENV'
        else:
            pillar_code = 'ENV'

        # Resolve framework if needed
        framework = None
        if options['framework_id'] or options['framework_code']:
            if options['framework_id']:
                try:
                    framework = RegulatoryFramework.objects.get(id=options['framework_id'])
                except RegulatoryFramework.DoesNotExist:
                    raise CommandError(f"Framework with ID {options['framework_id']} not found")
            elif options['framework_code']:
                try:
                    framework = RegulatoryFramework.objects.get(code__iexact=options['framework_code'])
                except RegulatoryFramework.DoesNotExist:
                    raise CommandError(f"Framework with code {options['framework_code']} not found")

        created_indicators = []
        created_mappings = 0
        fixtures = []
        next_pk = 1
        now = datetime.now(timezone.utc).isoformat()

        for i in range(options['count']):
            name = f"{options['pillar'] or 'Environmental'} {i+1}"
            code = f"IND_{i+1:04d}"
            unit = options['unit']
            data_type = options['data_type']

            self.stdout.write(f"Create Indicator: {name} (code={code}, unit={unit}, pillar={pillar_code})")

            if options['dry_run']:
                created_indicators.append(name)
                fixtures.append({
                    "model": "indicators.indicator",
                    "pk": next_pk,
                    "fields": {
                        "created_at": now,
                        "updated_at": now,
                        "name": name,
                        "code": code,
                        "pillar": pillar_code,
                        "data_type": data_type,
                        "unit": unit,
                        "description": "Auto-generated indicator"
                    },
                })
                next_pk += 1
                continue

            try:
                ind = Indicator.objects.create(
                    name=name,
                    code=code,
                    pillar=pillar_code,
                    data_type=data_type,
                    unit=unit,
                    description='Auto-generated indicator'
                )
                created_indicators.append(ind.id)
                fixtures.append({
                    "model": "indicators.indicator",
                    "pk": ind.id,
                    "fields": {
                        "created_at": ind.created_at.isoformat() if ind.created_at else now,
                        "updated_at": ind.updated_at.isoformat() if ind.updated_at else now,
                        "name": ind.name,
                        "code": ind.code,
                        "pillar": ind.pillar,
                        "data_type": ind.data_type,
                        "unit": ind.unit,
                        "description": ind.description
                    },
                })

                # Create mappings if requested
                if options['create_mappings']:
                    # Create OrganizationIndicator mapping
                    if org:
                        try:
                            org_ind = OrganizationIndicator.objects.create(
                                organization=org,
                                indicator=ind,
                                is_active=True
                            )
                            created_mappings += 1
                            self.stdout.write(f"  Created OrganizationIndicator for {org.name}")
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"  Failed to create OrganizationIndicator: {e}"))

                    # Create FrameworkIndicator mapping if framework specified
                    if framework:
                        try:
                            fw_ind = FrameworkIndicator.objects.create(
                                framework=framework,
                                indicator=ind,
                                is_active=True
                            )
                            created_mappings += 1
                            self.stdout.write(f"  Created FrameworkIndicator for {framework.name}")
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"  Failed to create FrameworkIndicator: {e}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create Indicator: {e}"))
                continue

        # write fixtures file if requested
        if options['fixtures']:
            out_path = options['fixtures']
            self.stdout.write(f"Writing fixtures to {out_path} ({len(fixtures)} objects)")
            try:
                with open(out_path, 'w') as fh:
                    json.dump(fixtures, fh, cls=DjangoJSONEncoder, indent=2)
                self.stdout.write(self.style.SUCCESS(f"Fixtures written to {out_path}"))
            except Exception as e:
                raise CommandError(f"Failed to write fixtures: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Created {len(created_indicators)} indicators, {created_mappings} mappings.'
            )
        )

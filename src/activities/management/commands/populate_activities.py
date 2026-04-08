"""Management command: Create ActivityType entries and optionally submit ActivitySubmission rows.

Usage:
  ./manage.py populate_activities --org-id 1 --count 20 --activity-prefix "Energy" --value-min 10 --value-max 100 --fixtures tmp/activities.json
"""
import uuid
import random
import json
from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from activities.models.activity_type import ActivityType
from activities.models.scope import Scope
from organizations.models import Organization
from submissions.services.activity import submit_activity_value
from accounts.models import User


class Command(BaseCommand):
    help = 'Populate ActivityTypes and optionally ActivitySubmission rows'

    def add_arguments(self, parser):
        parser.add_argument('--org-id', type=str, required=True, help='Organization ID (UUID or name substring match)')
        parser.add_argument('--reporting-period-id', type=int, help='Reporting period ID for submissions')
        parser.add_argument('--count', type=int, default=10, help='Number of activity submissions to create')
        parser.add_argument('--activity-prefix', type=str, default='AutoActivity', help='Name prefix for activity types')
        parser.add_argument('--scope-code', type=str, default=None, help='Scope code to attach ActivityType to')
        parser.add_argument('--unit', type=str, default='kgCO2', help='Unit string for activity type')
        parser.add_argument('--submit', action='store_true', help='Actually submit ActivitySubmission rows')
        parser.add_argument('--user-id', type=int, help='User ID to attribute submissions to')
        parser.add_argument('--username', type=str, help='Username to attribute submissions to')
        parser.add_argument('--facility-id', type=int, help='Facility ID for submissions')
        parser.add_argument('--value-min', type=float, default=1.0, help='Minimum value for random activity values')
        parser.add_argument('--value-max', type=float, default=100.0, help='Maximum value for random activity values')
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

        scope = None
        if options['scope_code']:
            scope = Scope.objects.filter(code=options['scope_code']).first()
        if scope is None:
            # Try to get or create a default scope
            scope, _ = Scope.objects.get_or_create(
                code='DEFAULT',
                defaults={'name': 'Default Scope', 'description': 'Default scope for activity types'}
            )

        created_types = []
        created_subs = 0
        fixtures = []
        next_pk = 1
        now = datetime.now(timezone.utc).isoformat()

        for i in range(options['count']):
            name = f"{options['activity_prefix']} {i+1}"
            unit = options['unit']
            self.stdout.write(f"Create ActivityType: {name} (unit={unit}, scope={scope})")

            if options['dry_run']:
                created_types.append(name)
                # generate fixture entry for dry-run as well
                fixtures.append({
                    "model": "activities.activitytype",
                    "pk": next_pk,
                    "fields": {
                        "created_at": now,
                        "updated_at": now,
                        "name": name,
                        "unit": unit,
                        "scope": scope.id if scope else None,
                        "description": "Auto-generated activity type"
                    },
                })
                next_pk += 1
                continue

            try:
                at = ActivityType.objects.create(
                    name=name,
                    unit=unit,
                    scope=scope,
                    description='Auto-generated activity type'
                )
                created_types.append(at.id)
                fixtures.append({
                    "model": "activities.activitytype",
                    "pk": at.id,
                    "fields": {
                        "created_at": at.created_at.isoformat() if at.created_at else now,
                        "updated_at": at.updated_at.isoformat() if at.updated_at else now,
                        "name": at.name,
                        "unit": at.unit,
                        "scope": at.scope.id if at.scope else None,
                        "description": at.description
                    },
                })
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create ActivityType: {e}"))
                continue

            if options['submit']:
                if not options['reporting_period_id']:
                    raise CommandError('--reporting-period-id is required when --submit is set')

                user = None
                if options['user_id']:
                    try:
                        user = User.objects.get(id=options['user_id'])
                    except User.DoesNotExist:
                        raise CommandError(f"User with ID {options['user_id']} not found")
                elif options['username']:
                    try:
                        user = User.objects.get(username=options['username'])
                    except User.DoesNotExist:
                        raise CommandError(f"User with username {options['username']} not found")
                else:
                    raise CommandError('--user-id or --username required for submissions')

                value = round(random.uniform(options['value_min'], options['value_max']), 3)
                self.stdout.write(f"Submitting activity value {value} for org={org.id} activity_type={at.id}")

                try:
                    submit_activity_value(
                        org=org,
                        user=user,
                        activity_type_id=str(at.id),
                        reporting_period_id=str(options['reporting_period_id']),
                        facility_id=options['facility_id'],
                        value=value,
                    )
                    created_subs += 1
                    fixtures.append({
                        "model": "submissions.activitysubmission",
                        "pk": str(uuid.uuid4()),
                        "fields": {
                            "organization": org.id,
                            "activity_type": at.id,
                            "reporting_period": options['reporting_period_id'],
                            "facility": options['facility_id'],
                            "value": value,
                            "created_by": user.id if user else None
                        },
                    })
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to submit activity: {e}"))
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
                f'Done. Created {len(created_types)} activity types, submitted {created_subs} submissions.'
            )
        )

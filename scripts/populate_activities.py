#!/usr/bin/env python3
"""[DEPRECATED] Use ./manage.py populate_activities instead.

Old script reference - replaced by Django management command for proper Django integration.

Legacy examples (no longer recommended):
  python ./scripts/populate_activities.py --org-id 1 --reporting-period-id 1 --count 20 --activity-prefix "Energy" --value-min 10 --value-max 100

Use instead:
  ./manage.py populate_activities --org-id 1 --reporting-period-id 1 --count 20 --activity-prefix "Energy" --value-min 10 --value-max 100

Parameters:
- --org-id / --org-slug (one required): organization to submit activity values for
- --reporting-period-id: reporting period id for submissions (required if --submit)
- --count: number of activity submissions to create
- --activity-prefix: name prefix for created ActivityType(s)
- --scope-code: code of an existing Scope to attach ActivityType to (defaults to 'DEFAULT' if present)
- --unit: unit string for activity type (default 'kgCO2')
- --submit: actually submit ActivitySubmission rows via submissions.services.activity.submit_activity_value
- --user-id or --username: user to attribute submissions to (required if --submit)
- --facility-id: optional facility id for submissions
- --dry-run: don't write to DB
"""
import argparse
import os
import sys
import uuid
import random
import json
from django.core.serializers.json import DjangoJSONEncoder


def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    import django

    django.setup()


def main():
    parser = argparse.ArgumentParser(description='Populate ActivityTypes and optionally ActivitySubmission rows')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--org-id', type=int)
    group.add_argument('--org-slug', type=str)
    parser.add_argument('--reporting-period-id', type=int)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--activity-prefix', type=str, default='AutoActivity')
    parser.add_argument('--scope-code', type=str, default=None)
    parser.add_argument('--unit', type=str, default='kgCO2')
    parser.add_argument('--submit', action='store_true')
    parser.add_argument('--user-id', type=int)
    parser.add_argument('--username', type=str)
    parser.add_argument('--facility-id', type=int)
    parser.add_argument('--value-min', type=float, default=1.0)
    parser.add_argument('--value-max', type=float, default=100.0)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--fixtures', type=str, help='Path to write Django JSON fixtures')
    args = parser.parse_args()

    setup_django()

    from activities.models.activity_type import ActivityType
    from activities.models.scope import Scope
    from organizations.models import Organization
    from submissions.services.activity import submit_activity_value
    from accounts.models import User

    if args.seed is not None:
        random.seed(args.seed)

    if args.org_id:
        org = Organization.objects.get(id=args.org_id)
    else:
        org = Organization.objects.get(slug=args.org_slug)

    scope = None
    if args.scope_code:
        scope = Scope.objects.filter(code=args.scope_code).first()
    if scope is None:
        scope = Scope.objects.first()

    created_types = []
    created_subs = 0
    fixtures = []
    next_pk = 1
    for i in range(args.count):
        name = f"{args.activity_prefix} {i+1}"
        unit = args.unit
        print(f"Create ActivityType: {name} (unit={unit}, scope={scope})")
        if args.dry_run:
            created_types.append(name)
            # generate fixture entry for dry-run as well
            fixtures.append({
                "model": "activities.activitytype",
                "pk": next_pk,
                "fields": {"name": name, "unit": unit, "scope": scope.id if scope else None, "description": "Auto-generated activity type"},
            })
            next_pk += 1
            continue
        at = ActivityType.objects.create(name=name, unit=unit, scope=scope, description='Auto-generated activity type')
        created_types.append(at.id)
        fixtures.append({
            "model": "activities.activitytype",
            "pk": at.id,
            "fields": {"name": at.name, "unit": at.unit, "scope": at.scope.id if at.scope else None, "description": at.description},
        })

        if args.submit:
            if not args.reporting_period_id:
                print('reporting-period-id is required when --submit is set')
                break
            user = None
            if args.user_id:
                user = User.objects.get(id=args.user_id)
            elif args.username:
                user = User.objects.get(username=args.username)
            else:
                print('user-id or username required for submissions')
                break

            value = round(random.uniform(args.value_min, args.value_max), 3)
            print(f"Submitting activity value {value} for org={org} activity_type={at.id}")
            if not args.dry_run:
                submit_activity_value(org=org, user=user, activity_type_id=str(at.id), reporting_period_id=str(args.reporting_period_id), facility_id=args.facility_id, value=value)
                created_subs += 1
                # attempt to create a simple fixture for the submission if model is predictable
                # fall back to a minimal representation referencing activity type by PK
                fixtures.append({
                    "model": "submissions.activitysubmission",
                    "pk": str(uuid.uuid4()),
                    "fields": {"organization": org.id, "activity_type": at.id, "reporting_period": args.reporting_period_id, "facility": args.facility_id, "value": value, "created_by": user.id if user else None},
                })

    # write fixtures file if requested
    if args.fixtures:
        out_path = args.fixtures
        print(f"Writing fixtures to {out_path} ({len(fixtures)} objects)")
        with open(out_path, 'w') as fh:
            json.dump(fixtures, fh, cls=DjangoJSONEncoder, indent=2)

    print(f"Done. Created {len(created_types)} activity types, submitted {created_subs} submissions.")


if __name__ == '__main__':
    main()

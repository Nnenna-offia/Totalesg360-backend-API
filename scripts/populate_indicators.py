#!/usr/bin/env python3
"""[DEPRECATED] Use ./manage.py populate_indicators instead.

Old script reference - replaced by Django management command for proper Django integration.

Legacy examples (no longer recommended):
  python ./scripts/populate_indicators.py --org-id 1 --count 10
  python ./scripts/populate_indicators.py --org-slug acme --count 5 --pillar ENV --data-type number --dry-run

Use instead:
  ./manage.py populate_indicators --org-id 1 --count 10
  ./manage.py populate_indicators --org-slug acme --count 5 --pillar Environmental --data-type numeric --dry-run

Parameters (legacy):
- --org-id / --org-slug (one required): organization to attach OrganizationIndicator rows to
- --count: number of indicators to create (default 10)
- --pillar: one of ENV, SOC, GOV (default random)
- --data-type: one of number, percent, boolean, text, currency (default number)
- --unit: optional unit string
- --framework-id / --framework-code: optional RegulatoryFramework to map indicators into via FrameworkIndicator
- --dry-run: don't write to DB, just print
- --seed: integer seed for reproducible output
"""
import argparse
import os
import sys
import uuid
import random


def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    import django

    django.setup()


def main():
    parser = argparse.ArgumentParser(description='Populate sample indicators and organization mappings')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--org-id', type=int)
    group.add_argument('--org-slug', type=str)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--pillar', choices=['ENV', 'SOC', 'GOV'])
    parser.add_argument('--data-type', choices=['number', 'percent', 'boolean', 'text', 'currency'], default='number')
    parser.add_argument('--unit', type=str, default='')
    parser.add_argument('--framework-id', type=int)
    parser.add_argument('--framework-code', type=str)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    setup_django()

    from indicators.models.indicator import Indicator, FrameworkIndicator, OrganizationIndicator
    from organizations.models import Organization
    from organizations.models import RegulatoryFramework

    if args.seed is not None:
        random.seed(args.seed)

    org = None
    if args.org_id:
        org = Organization.objects.get(id=args.org_id)
    else:
        org = Organization.objects.get(slug=args.org_slug)

    framework = None
    if args.framework_id:
        framework = RegulatoryFramework.objects.get(id=args.framework_id)
    elif args.framework_code:
        framework = RegulatoryFramework.objects.get(code=args.framework_code)

    created = []
    for i in range(args.count):
        code = f"AUTO_IND_{uuid.uuid4().hex[:8]}"
        name = f"Auto Indicator {code}"
        pillar = args.pillar or random.choice(['ENV', 'SOC', 'GOV'])
        data_type = args.data_type
        unit = args.unit or ("%" if data_type == 'percent' else ("units" if data_type == 'number' else ""))

        print(f"Creating Indicator: code={code} pillar={pillar} data_type={data_type} unit={unit}")
        if args.dry_run:
            created.append(code)
            continue

        ind = Indicator.objects.create(code=code, name=name, pillar=pillar, data_type=data_type, unit=unit)

        # Map to framework if provided
        if framework:
            FrameworkIndicator.objects.get_or_create(framework=framework, indicator=ind, defaults={'is_required': False, 'display_order': 100})

        # Create organization override/mapping
        OrganizationIndicator.objects.create(organization=org, indicator=ind, is_required=None, is_active=True)
        created.append(ind.code)

    print(f"Done. Created {len(created)} indicators.")


if __name__ == '__main__':
    main()

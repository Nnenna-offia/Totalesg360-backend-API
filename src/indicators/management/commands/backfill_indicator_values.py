"""Management command to backfill indicator values from existing activity submissions.

Usage:
    python manage.py backfill_indicator_values --org-id <uuid>
    python manage.py backfill_indicator_values --all
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from organizations.models import Organization
from submissions.models import ReportingPeriod
from indicators.services.indicator_aggregation import recalculate_all_indicators_for_period


class Command(BaseCommand):
    help = 'Backfill indicator values from existing activity submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=str,
            help='Organization ID (UUID) to backfill'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Backfill for all organizations'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        if not options['all'] and not options['org_id']:
            raise CommandError('Provide either --org-id or --all')

        if options['all']:
            orgs = Organization.objects.all()
        else:
            try:
                orgs = [Organization.objects.get(id=options['org_id'])]
            except Organization.DoesNotExist:
                raise CommandError(f"Organization {options['org_id']} not found")

        total_updated = 0

        for org in orgs:
            self.stdout.write(f"\nProcessing organization: {org.name} ({org.id})")
            
            periods = ReportingPeriod.objects.filter(organization=org)
            
            if not periods.exists():
                self.stdout.write(self.style.WARNING(f"  No reporting periods found"))
                continue
            
            for period in periods:
                self.stdout.write(f"  Period: {period.year} Q{period.quarter}")
                
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING("    [DRY RUN] Would recalculate indicators"))
                    continue
                
                try:
                    count = recalculate_all_indicators_for_period(
                        organization=org,
                        reporting_period=period
                    )
                    total_updated += count
                    self.stdout.write(self.style.SUCCESS(f"    Updated {count} indicator values"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    Error: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Total indicator values updated: {total_updated}'
            )
        )

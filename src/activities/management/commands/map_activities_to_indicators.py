"""Management command to map existing ActivityTypes to Indicators.

Usage:
    python manage.py map_activities_to_indicators
    
This is an interactive command that helps you map each ActivityType
to its corresponding Indicator.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from activities.models import ActivityType
from indicators.models import Indicator


class Command(BaseCommand):
    help = 'Map ActivityTypes to their corresponding Indicators'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Attempt automatic mapping based on name matching'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        activity_types = ActivityType.objects.filter(indicator__isnull=True)
        
        if not activity_types.exists():
            self.stdout.write(self.style.SUCCESS('All ActivityTypes are already mapped to indicators'))
            return

        indicators = list(Indicator.objects.all().order_by('code'))
        
        self.stdout.write(f"\nFound {activity_types.count()} unmapped ActivityTypes")
        self.stdout.write(f"Available indicators: {len(indicators)}\n")

        if options['auto']:
            self._auto_map(activity_types, indicators, options['dry_run'])
        else:
            self._interactive_map(activity_types, indicators, options['dry_run'])

    def _auto_map(self, activity_types, indicators, dry_run):
        """Attempt automatic mapping based on keywords."""
        
        # Simple keyword mapping rules
        keyword_map = {
            'emission': ['ghg', 'scope1', 'scope2', 'scope3', 'emission'],
            'waste': ['waste', 'disposal'],
            'water': ['water', 'withdrawal', 'consumption'],
            'energy': ['energy', 'electricity', 'fuel'],
        }
        
        mapped_count = 0
        
        for at in activity_types:
            name_lower = at.name.lower()
            matched_indicator = None
            
            for ind in indicators:
                ind_name_lower = ind.name.lower()
                ind_code_lower = ind.code.lower()
                
                # Check if any keywords match
                for category, keywords in keyword_map.items():
                    if any(kw in name_lower for kw in keywords):
                        if any(kw in ind_name_lower or kw in ind_code_lower for kw in keywords):
                            matched_indicator = ind
                            break
                
                if matched_indicator:
                    break
            
            if matched_indicator:
                self.stdout.write(
                    f"  Mapping: {at.name} → {matched_indicator.code} ({matched_indicator.name})"
                )
                
                if not dry_run:
                    at.indicator = matched_indicator
                    at.save(update_fields=['indicator', 'updated_at'])
                    
                    # Set indicator to activity-based
                    if matched_indicator.collection_method != Indicator.CollectionMethod.ACTIVITY:
                        matched_indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
                        matched_indicator.save(update_fields=['collection_method', 'updated_at'])
                
                mapped_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"  No match found for: {at.name}")
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nMapped {mapped_count} ActivityTypes')
        )

    def _interactive_map(self, activity_types, indicators, dry_run):
        """Interactive mapping."""
        self.stdout.write(self.style.WARNING(
            '\nInteractive mode not yet implemented. Use --auto for automatic mapping.'
        ))
        self.stdout.write(
            'Or manually set indicator FK in Django admin or via shell.'
        )

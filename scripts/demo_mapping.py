#!/usr/bin/env python
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from activities.models import ActivityType
from indicators.models import Indicator

# Example: Map the first few ActivityTypes to GHG emissions indicator
ghg_indicator = Indicator.objects.filter(code__icontains='GHG').first()

if ghg_indicator:
    print(f"Found indicator: {ghg_indicator.code} - {ghg_indicator.name}")
    
    # Update indicator to be activity-based
    ghg_indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
    ghg_indicator.save()
    print(f"  Set to activity-based collection")
    
    # Map first 5 ActivityTypes to this indicator
    activities = ActivityType.objects.filter(indicator__isnull=True)[:5]
    mapped_count = 0
    
    for at in activities:
        at.indicator = ghg_indicator
        at.save()
        print(f"  Mapped: {at.name} → {ghg_indicator.code}")
        mapped_count += 1
    
    print(f"\nMapped {mapped_count} ActivityTypes to {ghg_indicator.code}")
else:
    print("No GHG indicator found")

# Show mapping summary
total = ActivityType.objects.count()
mapped = ActivityType.objects.filter(indicator__isnull=False).count()
unmapped = total - mapped

print(f"\nSummary:")
print(f"  Total ActivityTypes: {total}")
print(f"  Mapped: {mapped}")
print(f"  Unmapped: {unmapped}")

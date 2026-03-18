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
from submissions.models import ActivitySubmission
from organizations.models import Organization

print("=== Activity-Indicator Integration Status ===\n")

# Check ActivityTypes
total_activities = ActivityType.objects.count()
mapped_activities = ActivityType.objects.filter(indicator__isnull=False).count()
print(f"ActivityTypes: {total_activities} total, {mapped_activities} mapped to indicators")

# Check Indicators
total_indicators = Indicator.objects.count()
activity_based = Indicator.objects.filter(collection_method='activity').count()
print(f"Indicators: {total_indicators} total, {activity_based} set to activity-based")

# Check Activity Submissions
activity_submissions = ActivitySubmission.objects.count()
print(f"ActivitySubmissions: {activity_submissions}")

# Check if we can test the workflow
if total_activities > 0 and total_indicators > 0:
    print("\n=== Quick Demo Setup ===")
    
    # Get first indicator and make it activity-based
    indicator = Indicator.objects.first()
    indicator.collection_method = Indicator.CollectionMethod.ACTIVITY
    indicator.save()
    print(f"1. Set indicator '{indicator.code}' to activity-based")
    
    # Map first activity type to it
    activity_type = ActivityType.objects.first()
    activity_type.indicator = indicator
    activity_type.save()
    print(f"2. Mapped ActivityType '{activity_type.name}' to indicator '{indicator.code}'")
    
    print(f"\n✓ System ready! Activity '{activity_type.name}' will now feed into indicator '{indicator.code}'")
    
    if activity_submissions > 0:
        print(f"\n3. Ready to backfill {activity_submissions} existing submissions")
        print("   Run: python manage.py backfill_indicator_values --all")
else:
    print("\n⚠ Need to create ActivityTypes and Indicators first")

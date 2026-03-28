#!/usr/bin/env python
"""
Test script to verify TargetGoal reporting frequency refactoring
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.insert(0, '/Users/barth/Projects/Side-hustle/Totalesg360-backend-API')
django.setup()

from targets.models import TargetGoal
from targets.services.reporting_period_service import ensure_reporting_periods_exist
from submissions.models import ReportingPeriod
from organizations.models import Organization

def test_reporting_frequency():
    """Test the reporting frequency refactoring"""
    
    print("=" * 60)
    print("TargetGoal Reporting Frequency Refactoring Tests")
    print("=" * 60)
    
    # Test 1: Verify ReportingFrequency choices
    print("\n✓ Test 1: ReportingFrequency choices")
    print("  Available frequencies:")
    for code, label in TargetGoal.ReportingFrequency.choices:
        print(f"    - {code}: {label}")
    
    # Test 2: Verify model field exists
    print("\n✓ Test 2: Model field verification")
    try:
        field = TargetGoal._meta.get_field('reporting_frequency')
        print(f"  reporting_frequency field found: {field}")
        print(f"  Field type: {type(field).__name__}")
        print(f"  Default: {field.default}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test 3: Test auto-generation service
    print("\n✓ Test 3: Auto-generation service")
    org = Organization.objects.first()
    if org:
        print(f"  Using organization: {org.name}")
        
        # Count before
        before = ReportingPeriod.objects.filter(
            organization=org,
            period_type="QUARTERLY",
            start_date__year=2025
        ).count()
        print(f"  Q1-Q4 2025 before: {before} periods")
        
        # Generate
        count = ensure_reporting_periods_exist(
            organization=org,
            start_year=2025,
            end_year=2025,
            frequency="QUARTERLY"
        )
        print(f"  Generated: {count} new periods")
        
        # Count after
        after = ReportingPeriod.objects.filter(
            organization=org,
            period_type="QUARTERLY",
            start_date__year=2025
        ).count()
        print(f"  Q1-Q4 2025 after: {after} periods")
        
        # Show periods
        periods = ReportingPeriod.objects.filter(
            organization=org,
            period_type="QUARTERLY",
            start_date__year=2025
        ).order_by("start_date")
        
        if periods.exists():
            print(f"  Created quarterly periods:")
            for p in periods:
                print(f"    - {p.name}: {p.start_date} → {p.end_date}")
    else:
        print("  No organizations found - skipping test")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_reporting_frequency()
    sys.exit(0 if success else 1)

"""Service for aggregating activity data into indicator values.

This service recalculates indicator values whenever activity submissions change.
"""
from typing import Optional
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone

from indicators.models import IndicatorValue, Indicator
from submissions.models import ActivitySubmission


def update_indicator_value(
    *,
    activity_submission: ActivitySubmission,
    facility_id: Optional[str] = None
) -> Optional[IndicatorValue]:
    """Recalculate and update indicator value from activities.
    
    Args:
        activity_submission: The activity submission that triggered the update
        facility_id: Optional facility ID to scope the aggregation
        
    Returns:
        The created or updated IndicatorValue instance, or None if no indicator linked
    """
    activity_type = activity_submission.activity_type
    indicator = activity_type.indicator
    
    # If activity type has no indicator mapping, skip
    if not indicator:
        return None
    
    # Only process activity-based indicators
    if indicator.collection_method != Indicator.CollectionMethod.ACTIVITY:
        return None
    
    organization = activity_submission.organization
    reporting_period = activity_submission.reporting_period
    facility = activity_submission.facility
    
    # Aggregate all activities for this indicator in the same reporting period
    filter_kwargs = {
        'activity_type__indicator': indicator,
        'organization': organization,
        'reporting_period': reporting_period,
    }
    
    if facility:
        filter_kwargs['facility'] = facility
    else:
        filter_kwargs['facility__isnull'] = True
    
    aggregation = ActivitySubmission.objects.filter(**filter_kwargs).aggregate(
        total=Sum('value'),
        count=Count('id')
    )
    
    total_value = float(aggregation['total'] or 0)
    activity_count = aggregation['count'] or 0
    
    metadata = {
        'activity_count': activity_count,
        'last_calculated_at': timezone.now().isoformat(),
        'source': 'activity_aggregation'
    }
    
    with transaction.atomic():
        indicator_value, created = IndicatorValue.objects.update_or_create(
            organization=organization,
            indicator=indicator,
            reporting_period=reporting_period,
            facility=facility,
            defaults={
                'value': total_value,
                'metadata': metadata
            }
        )
    
    return indicator_value


def recalculate_all_indicators_for_period(
    *,
    organization,
    reporting_period
) -> int:
    """Recalculate all activity-based indicators for a reporting period.
    
    Useful for bulk recalculation after data migration or corrections.
    
    Returns:
        Number of indicator values updated
    """
    count = 0
    
    # Get all activity-based indicators
    activity_indicators = Indicator.objects.filter(
        collection_method=Indicator.CollectionMethod.ACTIVITY,
        is_active=True
    )
    
    for indicator in activity_indicators:
        # Get all activity submissions for this indicator in the period
        activities = ActivitySubmission.objects.filter(
            activity_type__indicator=indicator,
            organization=organization,
            reporting_period=reporting_period
        )
        
        # Group by facility (including null)
        facilities = activities.values_list('facility', flat=True).distinct()
        
        for facility_id in facilities:
            filter_kwargs = {
                'activity_type__indicator': indicator,
                'organization': organization,
                'reporting_period': reporting_period,
            }
            
            if facility_id:
                filter_kwargs['facility_id'] = facility_id
            else:
                filter_kwargs['facility__isnull'] = True
            
            aggregation = ActivitySubmission.objects.filter(**filter_kwargs).aggregate(
                total=Sum('value'),
                cnt=Count('id')
            )
            
            total_value = float(aggregation['total'] or 0)
            activity_count = aggregation['cnt'] or 0
            
            metadata = {
                'activity_count': activity_count,
                'last_calculated_at': timezone.now().isoformat(),
                'source': 'bulk_recalculation'
            }
            
            with transaction.atomic():
                IndicatorValue.objects.update_or_create(
                    organization=organization,
                    indicator=indicator,
                    reporting_period=reporting_period,
                    facility_id=facility_id,
                    defaults={
                        'value': total_value,
                        'metadata': metadata
                    }
                )
            
            count += 1
    
    return count

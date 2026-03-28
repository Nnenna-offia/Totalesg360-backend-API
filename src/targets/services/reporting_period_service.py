"""
Reporting Period Service for Targets

Ensures reporting periods exist for target goals across multiple years.
Auto-generates missing periods to support multi-year target tracking.
"""
from typing import List
from submissions.models import ReportingPeriod
from submissions.services.period_generation import generate_reporting_periods


def ensure_reporting_periods_exist(
    organization,
    start_year: int,
    end_year: int,
    frequency: str
) -> int:
    """
    Ensure ReportingPeriods exist for all years in a target's range.
    
    If periods are missing for a given year, auto-generates them.
    
    Args:
        organization: Organization instance
        start_year: First year to ensure periods for
        end_year: Last year to ensure periods for (inclusive)
        frequency: Reporting frequency (e.g., "QUARTERLY", "ANNUAL")
        
    Returns:
        Number of new periods generated
        
    Example:
        ensure_reporting_periods_exist(
            organization=my_org,
            start_year=2025,
            end_year=2028,
            frequency="QUARTERLY"
        )
        # Generates Q1-Q4 for 2025, 2026, 2027, 2028 if missing
    """
    # Get all existing years for this org+frequency combination
    existing_years = set(
        ReportingPeriod.objects.filter(
            organization=organization,
            period_type=frequency
        ).values_list("start_date__year", flat=True).distinct()
    )
    
    total_generated = 0
    
    # Generate missing years
    for year in range(start_year, end_year + 1):
        if year not in existing_years:
            try:
                result = generate_reporting_periods(
                    organization=organization,
                    year=year,
                    period_types=[frequency],
                    save=True
                )
                # Count newly created periods
                total_generated += len(result.get(frequency, []))
            except Exception as e:
                # Log but don't fail - allow target to use existing periods
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to generate {frequency} periods for org {organization.id} year {year}: {str(e)}"
                )
                continue
    
    return total_generated

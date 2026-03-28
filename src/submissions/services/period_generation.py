"""
Reporting Period Generation Service

Auto-generates reporting periods for ESG data collection across different frequencies.
Supports daily, weekly, bi-weekly, monthly, quarterly, semi-annual, and annual periods.
"""
from datetime import date, timedelta
from typing import List, Dict, Any
from django.core.exceptions import ValidationError
from submissions.models import ReportingPeriod


def generate_weekly_periods(organization, year: int) -> List[ReportingPeriod]:
    """
    Generate 52 weekly periods for a given year.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
    
    Returns:
        List of ReportingPeriod instances (unsaved)
    """
    periods = []
    start_of_year = date(year, 1, 1)
    
    # Find the Monday of the first week
    days_since_monday = start_of_year.weekday()
    if days_since_monday > 0:
        start_date = start_of_year - timedelta(days=days_since_monday)
    else:
        start_date = start_of_year
    
    for week_num in range(1, 53):
        end_date = start_date + timedelta(days=6)
        
        # Only include weeks that start in this year
        if start_date.year == year or (week_num == 1 and start_date.year == year - 1):
            period = ReportingPeriod(
                organization=organization,
                name=f"Week {week_num} {year}",
                period_type=ReportingPeriod.PeriodType.WEEKLY,
                start_date=start_date,
                end_date=end_date,
                status=ReportingPeriod.Status.OPEN,
                is_active=True
            )
            periods.append(period)
        
        start_date = end_date + timedelta(days=1)
        
        # Stop if we've moved into next year
        if start_date.year > year:
            break
    
    return periods


def generate_bi_weekly_periods(organization, year: int) -> List[ReportingPeriod]:
    """
    Generate 26 bi-weekly (2-week) periods for a given year.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
    
    Returns:
        List of ReportingPeriod instances (unsaved)
    """
    periods = []
    start_date = date(year, 1, 1)
    period_num = 1
    
    while start_date.year == year:
        end_date = start_date + timedelta(days=13)  # 14 days total
        
        period = ReportingPeriod(
            organization=organization,
            name=f"Bi-Week {period_num} {year}",
            period_type=ReportingPeriod.PeriodType.BI_WEEKLY,
            start_date=start_date,
            end_date=end_date,
            status=ReportingPeriod.Status.OPEN,
            is_active=True
        )
        periods.append(period)
        
        start_date = end_date + timedelta(days=1)
        period_num += 1
    
    return periods


def generate_monthly_periods(organization, year: int) -> List[ReportingPeriod]:
    """
    Generate 12 monthly periods for a given year.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
    
    Returns:
        List of ReportingPeriod instances (unsaved)
    """
    periods = []
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    
    for month in range(1, 13):
        start_date = date(year, month, 1)
        
        # Calculate last day of month
        if month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        period = ReportingPeriod(
            organization=organization,
            name=f"{month_names[month-1]} {year}",
            period_type=ReportingPeriod.PeriodType.MONTHLY,
            start_date=start_date,
            end_date=end_date,
            status=ReportingPeriod.Status.OPEN,
            is_active=True
        )
        periods.append(period)
    
    return periods


def generate_quarterly_periods(organization, year: int) -> List[ReportingPeriod]:
    """
    Generate 4 quarterly periods for a given year.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
    
    Returns:
        List of ReportingPeriod instances (unsaved)
    """
    periods = []
    quarters = [
        {"q": 1, "start_month": 1, "end_month": 3},
        {"q": 2, "start_month": 4, "end_month": 6},
        {"q": 3, "start_month": 7, "end_month": 9},
        {"q": 4, "start_month": 10, "end_month": 12},
    ]
    
    for quarter in quarters:
        q_num = quarter["q"]
        start_date = date(year, quarter["start_month"], 1)
        
        # Calculate last day of quarter
        end_month = quarter["end_month"]
        if end_month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, end_month + 1, 1) - timedelta(days=1)
        
        period = ReportingPeriod(
            organization=organization,
            name=f"Q{q_num} {year}",
            period_type=ReportingPeriod.PeriodType.QUARTERLY,
            start_date=start_date,
            end_date=end_date,
            status=ReportingPeriod.Status.OPEN,
            is_active=True
        )
        periods.append(period)
    
    return periods


def generate_semi_annual_periods(organization, year: int) -> List[ReportingPeriod]:
    """
    Generate 2 semi-annual (6-month) periods for a given year.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
    
    Returns:
        List of ReportingPeriod instances (unsaved)
    """
    periods = []
    
    # H1: Jan - Jun
    period_h1 = ReportingPeriod(
        organization=organization,
        name=f"H1 {year}",
        period_type=ReportingPeriod.PeriodType.SEMI_ANNUAL,
        start_date=date(year, 1, 1),
        end_date=date(year, 6, 30),
        status=ReportingPeriod.Status.OPEN,
        is_active=True
    )
    periods.append(period_h1)
    
    # H2: Jul - Dec
    period_h2 = ReportingPeriod(
        organization=organization,
        name=f"H2 {year}",
        period_type=ReportingPeriod.PeriodType.SEMI_ANNUAL,
        start_date=date(year, 7, 1),
        end_date=date(year, 12, 31),
        status=ReportingPeriod.Status.OPEN,
        is_active=True
    )
    periods.append(period_h2)
    
    return periods


def generate_annual_period(organization, year: int) -> ReportingPeriod:
    """
    Generate 1 annual period for a given year.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
    
    Returns:
        ReportingPeriod instance (unsaved)
    """
    return ReportingPeriod(
        organization=organization,
        name=f"{year}",
        period_type=ReportingPeriod.PeriodType.ANNUAL,
        start_date=date(year, 1, 1),
        end_date=date(year, 12, 31),
        status=ReportingPeriod.Status.OPEN,
        is_active=True
    )


def generate_reporting_periods(
    organization,
    year: int,
    period_types: List[str],
    save: bool = True
) -> Dict[str, List[ReportingPeriod]]:
    """
    Main service function to generate reporting periods for an organization.
    
    Args:
        organization: Organization instance
        year: Year to generate periods for
        period_types: List of period types to generate (e.g., ["WEEKLY", "MONTHLY", "QUARTERLY"])
        save: Whether to save the periods to database (default: True)
    
    Returns:
        Dictionary mapping period_type to list of created periods
        
    Example:
        periods = generate_reporting_periods(
            organization=my_org,
            year=2025,
            period_types=["MONTHLY", "QUARTERLY", "ANNUAL"],
            save=True
        )
        # Returns: {
        #     "MONTHLY": [12 monthly periods],
        #     "QUARTERLY": [4 quarterly periods],
        #     "ANNUAL": [1 annual period]
        # }
    """
    results = {}
    generators = {
        "WEEKLY": generate_weekly_periods,
        "BI_WEEKLY": generate_bi_weekly_periods,
        "MONTHLY": generate_monthly_periods,
        "QUARTERLY": generate_quarterly_periods,
        "SEMI_ANNUAL": generate_semi_annual_periods,
        "ANNUAL": lambda org, yr: [generate_annual_period(org, yr)],
    }
    
    for period_type in period_types:
        if period_type not in generators:
            raise ValidationError(f"Invalid period_type: {period_type}. "
                                f"Must be one of: {list(generators.keys())}")
        
        generator_func = generators[period_type]
        periods = generator_func(organization, year)
        
        if save:
            # Bulk create all periods
            saved_periods = ReportingPeriod.objects.bulk_create(
                periods,
                ignore_conflicts=True  # Skip duplicates
            )
            results[period_type] = saved_periods
        else:
            results[period_type] = periods
    
    return results


def generate_custom_period(
    organization,
    name: str,
    start_date: date,
    end_date: date,
    save: bool = True
) -> ReportingPeriod:
    """
    Create a custom reporting period with specific dates.
    
    Args:
        organization: Organization instance
        name: Human-readable name for the period
        start_date: Start date of the period
        end_date: End date of the period
        save: Whether to save the period to database (default: True)
    
    Returns:
        ReportingPeriod instance
        
    Example:
        period = generate_custom_period(
            organization=my_org,
            name="Project Phase 1",
            start_date=date(2025, 3, 15),
            end_date=date(2025, 9, 30),
            save=True
        )
    """
    if start_date >= end_date:
        raise ValidationError("start_date must be before end_date")
    
    period = ReportingPeriod(
        organization=organization,
        name=name,
        period_type=ReportingPeriod.PeriodType.CUSTOM,
        start_date=start_date,
        end_date=end_date,
        status=ReportingPeriod.Status.OPEN,
        is_active=True
    )
    
    if save:
        period.save()
    
    return period

from calendar import month_abbr
from datetime import date, timedelta

from django.db import transaction

from organizations.models import Organization, OrganizationESGSettings
from submissions.models import ReportingPeriod


def get_or_create_esg_settings(organization: Organization) -> OrganizationESGSettings:
    defaults = {
        "reporting_level": organization.entity_type or Organization.EntityType.SUBSIDIARY,
    }
    settings, _ = OrganizationESGSettings.objects.get_or_create(
        organization=organization,
        defaults=defaults,
    )
    return settings


def add_months(value: date, months: int) -> date:
    month_index = (value.month - 1) + months
    year = value.year + month_index // 12
    month = (month_index % 12) + 1
    return date(year, month, 1)


def get_fiscal_year_start(settings: OrganizationESGSettings, today: date | None = None) -> date:
    today = today or date.today()
    year = today.year if today.month >= settings.fiscal_year_start_month else today.year - 1
    return date(year, settings.fiscal_year_start_month, 1)


def calculate_period_bounds(settings: OrganizationESGSettings, today: date | None = None) -> dict:
    today = today or date.today()
    fiscal_year_start = get_fiscal_year_start(settings, today=today)
    frequency = settings.reporting_frequency

    if frequency == ReportingPeriod.PeriodType.DAILY:
        return {
            "name": today.strftime("%Y-%m-%d"),
            "start_date": today,
            "end_date": today,
            "year": today.year,
            "quarter": None,
        }

    if frequency == ReportingPeriod.PeriodType.WEEKLY:
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return {
            "name": f"Week of {start_date.isoformat()}",
            "start_date": start_date,
            "end_date": end_date,
            "year": start_date.year,
            "quarter": None,
        }

    if frequency == ReportingPeriod.PeriodType.BI_WEEKLY:
        offset_days = (today - fiscal_year_start).days
        cycle_start = fiscal_year_start + timedelta(days=(offset_days // 14) * 14)
        cycle_end = cycle_start + timedelta(days=13)
        return {
            "name": f"Bi-Week of {cycle_start.isoformat()}",
            "start_date": cycle_start,
            "end_date": cycle_end,
            "year": cycle_start.year,
            "quarter": None,
        }

    if frequency == ReportingPeriod.PeriodType.MONTHLY:
        start_date = today.replace(day=1)
        end_date = add_months(start_date, 1) - timedelta(days=1)
        return {
            "name": f"{month_abbr[start_date.month]} {start_date.year}",
            "start_date": start_date,
            "end_date": end_date,
            "year": start_date.year,
            "quarter": None,
        }

    if frequency == ReportingPeriod.PeriodType.QUARTERLY:
        offset_months = (today.year - fiscal_year_start.year) * 12 + (today.month - fiscal_year_start.month)
        quarter_index = offset_months // 3
        start_date = add_months(fiscal_year_start, quarter_index * 3)
        end_date = add_months(start_date, 3) - timedelta(days=1)
        return {
            "name": f"Q{quarter_index + 1} {start_date.year}",
            "start_date": start_date,
            "end_date": end_date,
            "year": start_date.year,
            "quarter": quarter_index + 1,
        }

    if frequency == ReportingPeriod.PeriodType.SEMI_ANNUAL:
        second_half_start = add_months(fiscal_year_start, 6)
        start_date = second_half_start if today >= second_half_start else fiscal_year_start
        end_date = add_months(start_date, 6) - timedelta(days=1)
        half = 2 if start_date == second_half_start else 1
        return {
            "name": f"H{half} {start_date.year}",
            "start_date": start_date,
            "end_date": end_date,
            "year": start_date.year,
            "quarter": None,
        }

    fiscal_year_end = add_months(fiscal_year_start, 12) - timedelta(days=1)
    return {
        "name": f"FY {fiscal_year_start.year}/{fiscal_year_end.year}",
        "start_date": fiscal_year_start,
        "end_date": fiscal_year_end,
        "year": fiscal_year_start.year,
        "quarter": None,
    }


@transaction.atomic
def ensure_reporting_period(settings: OrganizationESGSettings) -> ReportingPeriod:
    bounds = calculate_period_bounds(settings)
    organization = settings.organization

    candidate = ReportingPeriod.objects.filter(
        organization=organization,
        period_type=settings.reporting_frequency,
        start_date=bounds["start_date"],
        end_date=bounds["end_date"],
    ).first()

    ReportingPeriod.objects.filter(
        organization=organization,
        period_type=settings.reporting_frequency,
        is_active=True,
    ).exclude(id=getattr(candidate, "id", None)).update(is_active=False)

    if candidate:
        updates = []
        for field_name, value in {
            "name": bounds["name"],
            "year": bounds["year"],
            "quarter": bounds["quarter"],
            "is_active": True,
        }.items():
            if getattr(candidate, field_name) != value:
                setattr(candidate, field_name, value)
                updates.append(field_name)
        if updates:
            candidate.save(update_fields=updates)
        return candidate

    return ReportingPeriod.objects.create(
        organization=organization,
        name=bounds["name"],
        period_type=settings.reporting_frequency,
        start_date=bounds["start_date"],
        end_date=bounds["end_date"],
        status=ReportingPeriod.Status.OPEN,
        is_active=True,
        year=bounds["year"],
        quarter=bounds["quarter"],
    )


def get_active_reporting_period(organization: Organization) -> ReportingPeriod | None:
    settings = get_or_create_esg_settings(organization)
    period = ReportingPeriod.objects.filter(
        organization=organization,
        period_type=settings.reporting_frequency,
        is_active=True,
    ).order_by("-start_date").first()
    if period:
        return period
    return ensure_reporting_period(settings)


def get_reporting_entities(organization: Organization):
    settings = get_or_create_esg_settings(organization)
    level = settings.reporting_level

    if level == Organization.EntityType.GROUP:
        return Organization.objects.filter(id=organization.id)

    if level == Organization.EntityType.SUBSIDIARY:
        return organization.children.filter(entity_type=Organization.EntityType.SUBSIDIARY, is_active=True)

    if level == Organization.EntityType.FACILITY:
        return Organization.objects.filter(
            parent__in=organization.children.all(),
            entity_type=Organization.EntityType.FACILITY,
            is_active=True,
        )

    descendant_ids = [org.id for org in organization.get_descendants(include_self=False)]
    return Organization.objects.filter(
        id__in=descendant_ids,
        entity_type=Organization.EntityType.DEPARTMENT,
        is_active=True,
    )
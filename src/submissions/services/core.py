from typing import Tuple, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError

from accounts.selectors.org_context import get_user_membership_for_org
from indicators.selectors.queries import get_org_effective_indicators
from organizations.models import Facility
from submissions.models import DataSubmission, ReportingPeriod
from indicators.models import Indicator


CAP_SUBMIT = "indicator.manage"  # align with view permission requirement
CAP_MANAGE_PERIOD = "manage_period"
CAP_APPROVE = "approve_submission"


def _user_has_capability(user, org, cap_code: str) -> bool:
    # A user may have multiple memberships/roles within the same organization.
    # Consider all active memberships for the org and return True if any of
    # the membership roles grant the requested capability.
    if not user or not org:
        return False
    memberships = user.memberships.filter(organization=org, is_active=True).select_related('role')
    if not memberships.exists():
        return False

    # Check across all roles for the capability
    role_ids = [m.role_id for m in memberships if m.role_id]
    if not role_ids:
        return False

    from roles.models import RoleCapability
    return RoleCapability.objects.filter(role_id__in=role_ids, capability__code=cap_code, is_active=True).exists()


def _validate_indicator_active_for_org(org, indicator: Indicator) -> bool:
    return get_org_effective_indicators(org).filter(pk=indicator.pk, is_active_effective=True).exists()


def _validate_facility_belongs(org, facility: Optional[Facility]) -> None:
    if facility is None:
        return
    if facility.organization_id != org.id:
        raise ValidationError("Facility does not belong to organization")


def _normalize_and_assign_values(indicator: Indicator, value) -> dict:
    """Return a dict of value fields to set on DataSubmission based on indicator.data_type.

    - Ensures only the correct field is used.
    - Normalizes percent values (if value looks like 0-100, convert to fraction if desired).
    """
    data_type = indicator.data_type
    payload = {"value_number": None, "value_text": None, "value_boolean": None}

    if data_type in (Indicator.DataType.NUMBER, Indicator.DataType.PERCENT, Indicator.DataType.CURRENCY):
        try:
            num = float(value)
        except Exception:
            raise ValidationError("Value must be numeric for this indicator")
        # normalize percent: if percent and value > 1 and <=100, store fraction (0-1)
        if data_type == Indicator.DataType.PERCENT:
            if num > 1 and num <= 100:
                num = num / 100.0
        payload["value_number"] = num
        return payload

    if data_type == Indicator.DataType.BOOLEAN:
        if not isinstance(value, bool):
            raise ValidationError("Value must be boolean for this indicator")
        payload["value_boolean"] = value
        return payload

    if data_type == Indicator.DataType.TEXT:
        if value is None:
            raise ValidationError("Value must be provided for text indicator")
        payload["value_text"] = str(value)
        return payload

    raise ValidationError("Unsupported indicator data_type")


def submit_indicator_value(*, org, user, indicator_id: str, reporting_period_id: str, facility_id: Optional[str] = None, value=None, metadata: Optional[dict] = None) -> Tuple[DataSubmission, bool]:
    """Validate and upsert a DataSubmission record.

    Returns (instance, created_bool).
    """
    # Resolve models
    try:
        indicator = Indicator.objects.get(id=indicator_id)
    except Indicator.DoesNotExist:
        raise ValidationError("Indicator not found")

    # Block direct submission for activity-derived indicators
    if indicator.collection_method == "activity":
        raise ValidationError(
            "This indicator is activity-derived and cannot be submitted directly. "
            "Please submit activity data instead."
        )

    try:
        period = ReportingPeriod.objects.get(id=reporting_period_id, organization=org)
    except ReportingPeriod.DoesNotExist:
        raise ValidationError("ReportingPeriod not found for organization")

    if period.status != ReportingPeriod.Status.OPEN:
        raise PermissionDenied("Reporting period is not open for edits")

    if not _validate_indicator_active_for_org(org, indicator):
        raise ValidationError("Indicator is not active for this organization")

    facility = None
    if facility_id:
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise ValidationError("Facility not found")
        _validate_facility_belongs(org, facility)

    # Validate capability
    if not _user_has_capability(user, org, CAP_SUBMIT):
        raise PermissionDenied("User lacks capability to submit indicators")

    # Validate value according to indicator type
    value_fields = _normalize_and_assign_values(indicator, value)

    defaults = {
        "value_number": value_fields.get("value_number"),
        "value_text": value_fields.get("value_text"),
        "value_boolean": value_fields.get("value_boolean"),
        "metadata": metadata or {},
        "status": DataSubmission.Status.DRAFT,
        "submitted_by": user,
        "submitted_at": timezone.now(),
    }

    with transaction.atomic():
        obj, created = DataSubmission.objects.update_or_create(
            organization=org,
            indicator=indicator,
            reporting_period=period,
            facility=facility,
            defaults=defaults,
        )

    return obj, created


def finalize_period(*, org, user, reporting_period_id: str) -> None:
    """Finalize a reporting period: validate permissions, ensure required indicators present, and lock period."""
    try:
        period = ReportingPeriod.objects.get(id=reporting_period_id, organization=org)
    except ReportingPeriod.DoesNotExist:
        raise ValidationError("ReportingPeriod not found for organization")

    if not _user_has_capability(user, org, CAP_MANAGE_PERIOD):
        raise PermissionDenied("User lacks capability to manage reporting periods")

    if period.status == ReportingPeriod.Status.LOCKED:
        return

    # Ensure all required indicators are present for this org & period
    required_qs = get_org_effective_indicators(org).filter(is_required_effective=True)
    required_ids = [r.id for r in required_qs]

    missing = []
    for ind_id in required_ids:
        exists = DataSubmission.objects.filter(organization=org, reporting_period=period, indicator_id=ind_id).exists()
        if not exists:
            missing.append(ind_id)

    if missing:
        raise ValidationError(f"Missing required indicator submissions: {missing}")

    # Lock the period
    period.lock(by_user=user)

    # Persist emission-derived indicators when a period is locked
    try:
        from emissions.services.persist_indicators import persist_emission_indicators
        # best-effort; do not break finalize if persistence fails
        try:
            persist_emission_indicators(org, period, by_user=user, submit=True)
        except Exception:
            pass
    except Exception:
        # emissions app may not be present in all deployments
        pass


def approve_submission(*, org, user, submission_id: str) -> DataSubmission:
    """Approve a finalized submission (requires capability)."""
    try:
        sub = DataSubmission.objects.get(id=submission_id, organization=org)
    except DataSubmission.DoesNotExist:
        raise ValidationError("Submission not found")

    if not _user_has_capability(user, org, CAP_APPROVE):
        raise PermissionDenied("User lacks capability to approve submissions")

    sub.mark_approved(by_user=user)
    return sub


def fetch_period_submissions(*, org, reporting_period_id: str, pillar: Optional[str] = None,
                             indicator_code: Optional[str] = None,
                             submission_status: Optional[str] = None,
                             facility_id: Optional[str] = None):
    """Return the list of indicator+submission summaries for a reporting period, applying filters."""
    try:
        period = ReportingPeriod.objects.get(id=reporting_period_id, organization=org)
    except ReportingPeriod.DoesNotExist:
        raise ValidationError("ReportingPeriod not found for organization")

    # Delegate to selector which handles prefetching and filtering
    from submissions.selectors.queries import get_period_submissions as _get_period_submissions

    return _get_period_submissions(org, period, pillar=pillar, indicator_code=indicator_code,
                                   submission_status=submission_status, facility_id=facility_id)

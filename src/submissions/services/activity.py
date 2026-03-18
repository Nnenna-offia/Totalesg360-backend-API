from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied

from submissions.models.activity_submission import ActivitySubmission
from submissions.models import ReportingPeriod
from activities.models.activity_type import ActivityType
from organizations.models.facility import Facility
from accounts.selectors.org_context import get_user_membership_for_org
from emissions.services.calculate_emission import calculate_and_store


def _user_is_org_member(user, org):
    membership = get_user_membership_for_org(user, org)
    return membership is not None


def submit_activity_value(*, org, user, activity_type_id: str, reporting_period_id: str, facility_id: Optional[str] = None, value=None, unit: str = None) -> ActivitySubmission:
    try:
        activity_type = ActivityType.objects.get(id=activity_type_id)
    except ActivityType.DoesNotExist:
        raise ValidationError("ActivityType not found")

    try:
        period = ReportingPeriod.objects.get(id=reporting_period_id, organization=org)
    except ReportingPeriod.DoesNotExist:
        raise ValidationError("ReportingPeriod not found for organization")

    if period.status != ReportingPeriod.Status.OPEN:
        raise PermissionDenied("Reporting period is not open for edits")

    facility = None
    if facility_id:
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise ValidationError("Facility not found")
        if facility.organization_id != org.id:
            raise ValidationError("Facility does not belong to organization")

    if not _user_is_org_member(user, org):
        raise PermissionDenied("User is not a member of the organization")

    # Basic validation of unit
    if unit is None:
        unit = activity_type.unit

    defaults = {
        'value': value,
        'unit': unit,
        'created_by': user,
    }

    with transaction.atomic():
        obj = ActivitySubmission.objects.create(
            organization=org,
            facility=facility,
            activity_type=activity_type,
            reporting_period=period,
            value=value,
            unit=unit,
            created_by=user,
        )

    # Trigger emission calculation (best effort)
    try:
        calculate_and_store(obj)
    except Exception:
        # do not fail submission if calculation errors; log later if needed
        pass

    # Trigger indicator aggregation if activity type is linked to an indicator
    try:
        from indicators.services.indicator_aggregation import update_indicator_value
        update_indicator_value(activity_submission=obj)
    except Exception:
        # do not fail submission if aggregation errors
        pass

    return obj

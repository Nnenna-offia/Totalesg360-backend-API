from typing import Optional
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from submissions.models.activity_submission import ActivitySubmission
from submissions.models import ReportingPeriod
from activities.models.activity_type import ActivityType
from organizations.models.facility import Facility
from accounts.selectors.org_context import get_user_membership_for_org
from emissions.services.calculate_emission import calculate_and_store
from submissions.services.reporting_period import get_or_raise_active_reporting_period
from targets.models import TargetGoal


def _user_is_org_member(user, org):
    membership = get_user_membership_for_org(user, org)
    return membership is not None


def submit_activity_value(*, org, user, activity_type_id: str, reporting_period_id: Optional[str] = None, facility_id: Optional[str] = None, value=None) -> ActivitySubmission:
    try:
        activity_type = ActivityType.objects.get(id=activity_type_id)
    except ActivityType.DoesNotExist:
        raise ValidationError("ActivityType not found")

    # Resolve reporting period from active ESG settings unless an internal caller
    # explicitly provides one.
    period = None
    if reporting_period_id:
        try:
            period = ReportingPeriod.objects.get(id=reporting_period_id, organization=org)
        except ReportingPeriod.DoesNotExist:
            raise ValidationError(detail="ReportingPeriod not found for organization")
    else:
        period = get_or_raise_active_reporting_period(org)

    if period.status != ReportingPeriod.Status.OPEN:
        raise PermissionDenied(detail="Reporting period is not open for edits")

    facility = None
    if facility_id:
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise ValidationError(detail="Facility not found")
        if facility.organization_id != org.id:
            raise ValidationError(detail="Facility does not belong to organization")

    if not _user_is_org_member(user, org):
        raise PermissionDenied(detail="User is not a member of the organization")


    defaults = {
        'value': value,
        'created_by': user,
    }

    # Prevent duplicate submissions for the same org/period/activity/facility
    exists = ActivitySubmission.objects.filter(
        organization=org,
        reporting_period=period,
        activity_type=activity_type,
        facility=facility,
    ).exists()

    if exists:
        raise ValidationError("Submission already exists for this reporting period")

    with transaction.atomic():
        obj = ActivitySubmission.objects.create(
            organization=org,
            facility=facility,
            activity_type=activity_type,
            reporting_period=period,
            value=value,
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

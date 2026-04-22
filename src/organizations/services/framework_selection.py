from django.core.exceptions import ValidationError
from django.db import transaction

from organizations.models import OrganizationFramework, RegulatoryFramework
from organizations.selectors.frameworks import get_framework_selection_options


def _normalize_primary_framework(organization):
    active_assignments = list(
        OrganizationFramework.objects.select_for_update()
        .filter(organization=organization, is_enabled=True)
        .select_related("framework")
        .order_by("-is_primary", "-framework__priority", "framework__name", "assigned_at")
    )

    if not active_assignments:
        OrganizationFramework.objects.filter(organization=organization, is_primary=True).update(is_primary=False)
        return

    primary = next((assignment for assignment in active_assignments if assignment.is_primary), active_assignments[0])
    OrganizationFramework.objects.filter(organization=organization, is_primary=True).exclude(id=primary.id).update(is_primary=False)
    if not primary.is_primary:
        primary.is_primary = True
        primary.save(update_fields=["is_primary"])


@transaction.atomic
def update_organization_frameworks(*, organization, updates, assigned_by=None):
    framework_ids = [item["framework_id"] for item in updates]
    unique_framework_ids = set(framework_ids)

    selectable_frameworks = {
        framework.id: framework
        for framework in RegulatoryFramework.objects.filter(
            id__in=unique_framework_ids,
            is_active=True,
            is_system=True,
        )
    }

    missing_framework_ids = unique_framework_ids.difference(selectable_frameworks.keys())
    if missing_framework_ids:
        raise ValidationError("One or more frameworks are invalid or not selectable")

    existing_assignments = {
        assignment.framework_id: assignment
        for assignment in OrganizationFramework.objects.select_for_update().filter(
            organization=organization,
            framework_id__in=unique_framework_ids,
        )
    }

    for item in updates:
        framework_id = item["framework_id"]
        is_active = item["is_active"]
        assignment = existing_assignments.get(framework_id)

        if assignment:
            update_fields = []
            if assignment.is_enabled != is_active:
                assignment.is_enabled = is_active
                update_fields.append("is_enabled")
            if not is_active and assignment.is_primary:
                assignment.is_primary = False
                update_fields.append("is_primary")
            if update_fields:
                assignment.save(update_fields=update_fields)
            continue

        OrganizationFramework.objects.create(
            organization=organization,
            framework=selectable_frameworks[framework_id],
            is_enabled=is_active,
            is_primary=False,
            assigned_by=assigned_by,
        )

    _normalize_primary_framework(organization)
    return get_framework_selection_options(organization)
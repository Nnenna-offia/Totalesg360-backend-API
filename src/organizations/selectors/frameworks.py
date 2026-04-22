from organizations.models import OrganizationFramework, RegulatoryFramework


def get_active_frameworks(org):
    return RegulatoryFramework.objects.filter(
        is_active=True,
        organization_assignments__organization=org,
        organization_assignments__is_enabled=True,
    ).distinct()


def get_framework_selection_options(org):
    assignments = {
        assignment.framework_id: assignment
        for assignment in OrganizationFramework.objects.filter(organization=org).select_related("framework")
    }

    options = []
    available_frameworks = RegulatoryFramework.objects.filter(
        is_active=True,
        is_system=True,
    ).order_by("-priority", "name")

    for framework in available_frameworks:
        assignment = assignments.get(framework.id)
        options.append(
            {
                "framework": framework,
                "assignment": assignment,
                "is_assigned": assignment is not None,
                "is_active": bool(assignment and assignment.is_enabled),
                "is_enabled": bool(assignment and assignment.is_enabled),
                "is_primary": bool(assignment and assignment.is_primary),
                "assigned_at": assignment.assigned_at if assignment else None,
            }
        )

    return options
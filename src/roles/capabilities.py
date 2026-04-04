# roles/capabilities.py

class Capabilities:
    # Organization capabilities
    ORG_MANAGE = "org.manage"
    ORG_INVITE_MEMBERS = "org.invite_members"
    ORG_MANAGE_FACILITIES = "org.manage_facilities"
    ORG_VIEW_MEMBERS = "org.view_members"
    DEPARTMENT_MANAGE = "department.manage"

    # Activity capabilities
    ACTIVITY_TYPE_VIEW = "activity_type.view"
    ACTIVITY_SUBMIT = "activity.submit"
    ACTIVITY_EDIT = "activity.edit"
    ACTIVITY_DELETE = "activity.delete"
    ACTIVITY_VIEW_SUBMISSIONS = "activity.view_submissions"

    # Emission capabilities
    EMISSION_VIEW = "emission.view"
    EMISSION_VIEW_SCOPE_BREAKDOWN = "emission.view_scope_breakdown"

    # Target capabilities
    TARGET_CREATE = "target.create"
    TARGET_EDIT = "target.edit"
    TARGET_DELETE = "target.delete"
    TARGET_VIEW = "target.view"

    # Indicator capabilities
    INDICATOR_VIEW = "indicator.view"
    # Submission approval
    APPROVE_SUBMISSION = "approve_submission"
    # Compliance capabilities
    COMPLIANCE_VIEW = "compliance.view"

    # Platform admin (global)
    SCOPE_MANAGE = "scope.manage"
    ACTIVITY_TYPE_MANAGE = "activity_type.manage"
    # Legacy/compatibility capability used in views
    MANAGE_ACTIVITY_TYPES = "manage_activity_types"
    EMISSION_FACTOR_MANAGE = "emission_factor.manage"
    INDICATOR_MANAGE = "indicator.manage"
    FRAMEWORK_MANAGE = "framework.manage"

    # backwards-compat / system operations
    MANAGE_ROLES = "manage_roles"
    # Reporting period management
    MANAGE_PERIOD = "manage_period"

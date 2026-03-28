# roles/role_capabilities.py
from .capabilities import Capabilities
ROLE_CAPABILITIES = {
    "org_owner": [
        Capabilities.ORG_MANAGE,
        Capabilities.ORG_INVITE_MEMBERS,
        Capabilities.ORG_MANAGE_FACILITIES,
        Capabilities.MANAGE_PERIOD,

        Capabilities.ACTIVITY_TYPE_VIEW,
        Capabilities.ACTIVITY_SUBMIT,
        Capabilities.ACTIVITY_EDIT,
        Capabilities.ACTIVITY_DELETE,
        Capabilities.ACTIVITY_VIEW_SUBMISSIONS,

        Capabilities.EMISSION_VIEW,
        Capabilities.EMISSION_VIEW_SCOPE_BREAKDOWN,

        Capabilities.TARGET_CREATE,
        Capabilities.TARGET_EDIT,
        Capabilities.TARGET_DELETE,
        Capabilities.TARGET_VIEW,

        Capabilities.INDICATOR_VIEW,
        Capabilities.COMPLIANCE_VIEW,
        Capabilities.INDICATOR_MANAGE,
        Capabilities.APPROVE_SUBMISSION,
    ],
    "sustainability_manager": [
        Capabilities.ACTIVITY_TYPE_VIEW,
        Capabilities.ACTIVITY_SUBMIT,
        Capabilities.ACTIVITY_EDIT,
        Capabilities.ACTIVITY_VIEW_SUBMISSIONS,

        Capabilities.EMISSION_VIEW,
        Capabilities.EMISSION_VIEW_SCOPE_BREAKDOWN,

        Capabilities.TARGET_CREATE,
        Capabilities.TARGET_EDIT,
        Capabilities.TARGET_VIEW,

        Capabilities.INDICATOR_VIEW,
        Capabilities.COMPLIANCE_VIEW,
    ],
    "data_contributor": [
        Capabilities.ACTIVITY_TYPE_VIEW,
        Capabilities.ACTIVITY_SUBMIT,
        Capabilities.ACTIVITY_EDIT,
        Capabilities.ACTIVITY_VIEW_SUBMISSIONS,

        Capabilities.EMISSION_VIEW,
        Capabilities.INDICATOR_VIEW,
    ],
    "viewer": [
        Capabilities.ACTIVITY_TYPE_VIEW,
        Capabilities.ACTIVITY_VIEW_SUBMISSIONS,

        Capabilities.EMISSION_VIEW,

        Capabilities.TARGET_VIEW,
        Capabilities.INDICATOR_VIEW,
    ],
}

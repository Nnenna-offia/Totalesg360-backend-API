# roles/role_capabilities.py
from .capabilities import Capabilities

ROLE_CAPABILITIES = {
    "org_admin": [
        Capabilities.MANAGE_ORGANIZATION,
        Capabilities.MANAGE_USERS,
        Capabilities.CONFIGURE_ESG,
        Capabilities.MANAGE_TARGETS,
        Capabilities.VIEW_DASHBOARDS,
    ],
    "environmental_officer": [
        Capabilities.SUBMIT_ENVIRONMENTAL,
        Capabilities.VIEW_DASHBOARDS,
    ],
    "social_officer": [
        Capabilities.SUBMIT_SOCIAL,
        Capabilities.VIEW_DASHBOARDS,
    ],
    "governance_officer": [
        Capabilities.SUBMIT_GOVERNANCE,
        Capabilities.VIEW_DASHBOARDS,
    ],
    "auditor": [
        Capabilities.REVIEW_SUBMISSIONS,
        Capabilities.VIEW_DASHBOARDS,
    ],
}

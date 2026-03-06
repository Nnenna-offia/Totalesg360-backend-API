# roles/capabilities.py

class Capabilities:
    # Organization
    MANAGE_ORGANIZATION = "manage_organization"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"

    # Configuration
    CONFIGURE_ESG = "configure_esg"
    MANAGE_TARGETS = "manage_targets"
    MANAGE_INDICATORS = "manage_indicators"

    # Data submission
    SUBMIT_ENVIRONMENTAL = "submit_environmental"
    SUBMIT_SOCIAL = "submit_social"
    SUBMIT_GOVERNANCE = "submit_governance"

    # Review
    VIEW_DASHBOARDS = "view_dashboards"
    REVIEW_SUBMISSIONS = "review_submissions"

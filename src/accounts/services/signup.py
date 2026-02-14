"""Signup service with organization creation and framework bootstrapping."""
import uuid
from typing import Dict, Any
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone

from common.exceptions import BadRequest, Conflict
from common.logging import get_service_logger
from accounts.utils.otp import create_and_send_otp_for_user
from accounts.selectors.user import user_exists_by_email
from organizations.models import (
    Organization,
    Membership,
    RegulatoryFramework,
    OrganizationFramework,
)
from organizations.selectors.metadata import organization_exists_by_name
from roles.models import Role

User = get_user_model()
logger = get_service_logger("signup")


def signup(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    organization_name: str,
    sector: str,
    country: str,
    primary_reporting_focus: str,
) -> Dict[str, Any]:
    """Create user account with organization and assign regulatory frameworks.
    
    Args:
        email: User email
        password: User password
        first_name: User first name
        last_name: User last name
        organization_name: Organization name
        sector: Organization sector
        country: Organization country code
        primary_reporting_focus: Primary reporting focus (NIGERIA/INTERNATIONAL/HYBRID)
    
    Returns:
        Dict with user and organization data
    
    Raises:
        BadRequest: Invalid input data
        Conflict: Email or organization name already exists
    """
    logger.info(
        "Signup initiated",
        extra={
            "email": email,
            "organization_name": organization_name,
            "sector": sector,
            "primary_reporting_focus": primary_reporting_focus,
        },
    )
    
    # Validate inputs
    _validate_signup_data(
        email=email,
        organization_name=organization_name,
        sector=sector,
        primary_reporting_focus=primary_reporting_focus,
    )
    
    with transaction.atomic():
        # Create user
        user = _create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Create organization
        organization = _create_organization(
            name=organization_name,
            sector=sector,
            country=country,
            primary_reporting_focus=primary_reporting_focus,
        )
        
        # Assign owner role
        owner_role = _get_or_create_owner_role()
        membership = _create_membership(
            user=user,
            organization=organization,
            role=owner_role,
            added_by=None,  # System assignment
        )
        
        # Bootstrap regulatory frameworks
        _assign_regulatory_frameworks(
            organization=organization,
            sector=sector,
            primary_reporting_focus=primary_reporting_focus,
            assigned_by=None,  # System assignment
        )
    # Create and send OTP for email verification (outside inner functions)
    otp_sent = False
    try:
        ev, otp_sent = create_and_send_otp_for_user(user, is_resend=False)
        if otp_sent:
            logger.info("OTP enqueued/sent", extra={"user_id": str(user.id), "email": user.email})
        else:
            logger.warning("OTP not sent/enqueued", extra={"user_id": str(user.id), "email": user.email})
    except Exception:
        # Do not fail signup if async send fails; user can request resend via API
        otp_sent = False
        logger.exception("Failed to create/send OTP email")
    logger.info(
        "Signup completed successfully",
        extra={
            "user_id": str(user.id),
            "organization_id": str(organization.id),
            "email": email,
        },
    )
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "organization_id": str(organization.id),
        "organization_name": organization.name,
        "sector": organization.sector,
        "primary_reporting_focus": organization.primary_reporting_focus,
        "verification_required": True,
        "otp_sent": bool(otp_sent),
    }


def _validate_signup_data(
    *, email: str, organization_name: str, sector: str, primary_reporting_focus: str
) -> None:
    """Validate signup inputs.
    
    Raises:
        BadRequest: Invalid data
        Conflict: Email or organization already exists
    """
    # Check email uniqueness
    if user_exists_by_email(email):
        logger.warning("Signup failed - email already exists", extra={"email": email})
        raise Conflict(detail=f"Email {email} is already registered")
    
    # Check organization name uniqueness
    if organization_exists_by_name(organization_name):
        logger.warning(
            "Signup failed - organization name already exists",
            extra={"organization_name": organization_name},
        )
        raise Conflict(detail=f"Organization name '{organization_name}' is already taken")
    
    # Validate sector
    valid_sectors = dict(Organization._meta.get_field("sector").choices).keys()
    if sector not in valid_sectors:
        raise BadRequest(
            detail=f"Invalid sector '{sector}'. Must be one of: {', '.join(valid_sectors)}"
        )
    
    # Validate primary reporting focus
    if primary_reporting_focus not in Organization.PrimaryReportingFocus.values:
        raise BadRequest(
            detail=f"Invalid primary_reporting_focus '{primary_reporting_focus}'. Must be one of: {', '.join(Organization.PrimaryReportingFocus.values)}"
        )


def _create_user(*, email: str, password: str, first_name: str, last_name: str) -> User:
    """Create user account."""
    user = User.objects.create_user(
        username=email,  # Use email as username
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    logger.info("User created", extra={"user_id": str(user.id), "email": email})
    return user


def _create_organization(
    *, name: str, sector: str, country: str, primary_reporting_focus: str
) -> Organization:
    """Create organization."""
    organization = Organization.objects.create(
        name=name,
        sector=sector,
        country=country,
        primary_reporting_focus=primary_reporting_focus,
        is_active=True,
    )
    logger.info(
        "Organization created",
        extra={
            "organization_id": str(organization.id),
            "organization_name": name,
            "sector": sector,
            "primary_reporting_focus": primary_reporting_focus,
        },
    )
    return organization


def _get_or_create_owner_role() -> Role:
    """Get or create organization owner role."""
    role, created = Role.objects.get_or_create(
        code="org_admin",
        defaults={
            "name": "Organization Administrator",
            "description": "Full control over organization",
            "is_system": True,
        },
    )
    if created:
        logger.info("Owner role created", extra={"role_code": role.code})
    return role


def _create_membership(*, user: User, organization: Organization, role: Role, added_by: User = None) -> Membership:
    """Create organization membership."""
    membership = Membership.objects.create(
        user=user,
        organization=organization,
        role=role,
        is_active=True,
        added_by=added_by,
    )
    logger.info(
        "Membership created",
        extra={
            "user_id": str(user.id),
            "organization_id": str(organization.id),
            "role": role.code,
        },
    )
    return membership


def _assign_regulatory_frameworks(
    *,
    organization: Organization,
    sector: str,
    primary_reporting_focus: str,
    assigned_by: User = None,
) -> None:
    """Bootstrap regulatory frameworks based on sector and reporting focus.
    
    Logic:
    - NIGERIA: Assign Nigerian frameworks (cross-sector + sector-specific)
    - INTERNATIONAL: Assign international frameworks (cross-sector only)
    - HYBRID: Assign both Nigerian and international frameworks
    """
    frameworks_to_assign = []
    
    if primary_reporting_focus in (Organization.PrimaryReportingFocus.NIGERIA, Organization.PrimaryReportingFocus.HYBRID):
        # Add Nigerian frameworks
        nigerian_frameworks = RegulatoryFramework.objects.filter(
            jurisdiction=RegulatoryFramework.Jurisdiction.NIGERIA,
            is_active=True,
        ).filter(
            models.Q(sector="") | models.Q(sector=sector)
        )
        frameworks_to_assign.extend(nigerian_frameworks)
        logger.info(
            f"Selected {nigerian_frameworks.count()} Nigerian frameworks",
            extra={"organization_id": str(organization.id), "sector": sector},
        )
    
    if primary_reporting_focus in (Organization.PrimaryReportingFocus.INTERNATIONAL, Organization.PrimaryReportingFocus.HYBRID):
        # Add international frameworks (cross-sector)
        international_frameworks = RegulatoryFramework.objects.filter(
            jurisdiction=RegulatoryFramework.Jurisdiction.INTERNATIONAL,
            is_active=True,
            sector="",  # Cross-sector only for signup
        )
        frameworks_to_assign.extend(international_frameworks)
        logger.info(
            f"Selected {international_frameworks.count()} international frameworks",
            extra={"organization_id": str(organization.id)},
        )
    
    # Assign frameworks (first one marked as primary)
    for idx, framework in enumerate(frameworks_to_assign):
        OrganizationFramework.objects.create(
            organization=organization,
            framework=framework,
            is_primary=(idx == 0),  # First framework is primary
            is_enabled=True,
            assigned_by=assigned_by,
        )
    
    logger.info(
        f"Assigned {len(frameworks_to_assign)} regulatory frameworks",
        extra={
            "organization_id": str(organization.id),
            "frameworks": [fw.code for fw in frameworks_to_assign],
        },
    )


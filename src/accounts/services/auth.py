"""Authentication business logic services."""
import uuid
from datetime import timedelta
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings

from common.exceptions import Unauthorized, BadRequest
from common.logging import get_service_logger
from accounts.models import RefreshToken
from accounts.auth.tokens import make_token

logger = get_service_logger("auth")


def authenticate_user(email: str, password: str):
    """Authenticate user credentials.
    
    Args:
        email: User email
        password: User password
    
    Returns:
        User instance if authentication succeeds
    
    Raises:
        Unauthorized: Invalid credentials
    """
    logger.info("Authentication attempt", extra={"email": email})
    
    user = authenticate(username=email, password=password)
    if not user:
        logger.warning("Authentication failed - invalid credentials", extra={"email": email})
        raise Unauthorized(detail="Invalid email or password")
    
    if not user.is_active:
        logger.warning("Authentication failed - inactive account", extra={"email": email, "user_id": str(user.id)})
        raise Unauthorized(detail="User account is disabled")
    
    logger.info("Authentication successful", extra={"email": email, "user_id": str(user.id)})
    return user


def create_access_token(user) -> str:
    """Create access token for authenticated user.
    
    Args:
        user: User instance
    
    Returns:
        Encoded JWT access token
    """
    # Get user's primary organization (assuming one-to-many via memberships)
    org_id = None
    roles = []
    
    # Get organization from first active membership
    membership = user.memberships.filter(is_active=True).select_related('organization', 'role').first()
    if membership:
        org_id = str(membership.organization.id)
        roles = [membership.role.name] if membership.role else []
    
    payload = {
        "user_id": str(user.id),
        "organization_id": org_id,
        "roles": roles,
    }
    
    lifetime = getattr(settings, "JWT_ACCESS_LIFETIME_SECONDS", 300)
    return make_token(payload, lifetime)


def create_refresh_token(user, ip_address: str = None, user_agent: str = None) -> tuple[str, str]:
    """Create refresh token and store allowlist record.
    
    Args:
        user: User instance
        ip_address: Client IP address (optional)
        user_agent: Client user agent (optional)
    
    Returns:
        Tuple of (refresh_token_jwt, jti)
    """
    jti = str(uuid.uuid4())
    lifetime = getattr(settings, "JWT_REFRESH_LIFETIME_SECONDS", 7 * 24 * 3600)
    
    payload = {"user_id": str(user.id)}
    token = make_token(payload, lifetime, jti=jti)
    
    # Store refresh token in database allowlist
    RefreshToken.objects.create(
        jti=jti,
        user=user,
        expires_at=timezone.now() + timedelta(seconds=lifetime),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return token, jti


def rotate_refresh_token(old_jti: str, user) -> tuple[str, str]:
    """Rotate refresh token by revoking old one and creating new.
    
    Args:
        old_jti: JWT ID of token being rotated
        user: User instance
    
    Returns:
        Tuple of (new_refresh_token_jwt, new_jti)
    
    Raises:
        Unauthorized: Old token not found or already revoked (possible reuse attack)
    """
    try:
        old_token_record = RefreshToken.objects.get(jti=old_jti, user=user)
    except RefreshToken.DoesNotExist:
        # Token not in allowlist - possible reuse attack
        logger.error(
            "Refresh token rotation failed - token not found (possible reuse attack)",
            extra={"jti": str(old_jti), "user_id": str(user.id)}
        )
        # Revoke all user's refresh tokens as security measure
        RefreshToken.objects.filter(user=user, revoked=False).update(revoked=True)
        raise Unauthorized(detail="Refresh token not recognized - all tokens revoked")
    
    if not old_token_record.is_active:
        # Token already used or expired - possible reuse attack
        logger.error(
            "Refresh token rotation failed - token already revoked/expired (possible reuse attack)",
            extra={"jti": str(old_jti), "user_id": str(user.id)}
        )
        RefreshToken.objects.filter(user=user, revoked=False).update(revoked=True)
        raise Unauthorized(detail="Refresh token expired or already used - all tokens revoked")
    
    # Create new refresh token
    new_jti = str(uuid.uuid4())
    lifetime = getattr(settings, "JWT_REFRESH_LIFETIME_SECONDS", 7 * 24 * 3600)
    payload = {"user_id": str(user.id)}
    new_token = make_token(payload, lifetime, jti=new_jti)
    
    # Store new token
    RefreshToken.objects.create(
        jti=new_jti,
        user=user,
        expires_at=timezone.now() + timedelta(seconds=lifetime),
        ip_address=old_token_record.ip_address,
        user_agent=old_token_record.user_agent,
    )
    
    # Revoke old token and link to new one
    old_token_record.revoked = True
    old_token_record.replaced_by = new_jti
    old_token_record.save(update_fields=["revoked", "replaced_by"])
    
    logger.info(
        "Refresh token rotated successfully",
        extra={"old_jti": str(old_jti), "new_jti": new_jti, "user_id": str(user.id)}
    )
    
    return new_token, new_jti


def revoke_refresh_token(jti: str):
    """Revoke a refresh token by JWT ID.
    
    Args:
        jti: JWT ID to revoke
    """
    RefreshToken.objects.filter(jti=jti).update(revoked=True)


def revoke_all_user_tokens(user):
    """Revoke all refresh tokens for a user (e.g., on logout all devices).
    
    Args:
        user: User instance
    """
    RefreshToken.objects.filter(user=user, revoked=False).update(revoked=True)

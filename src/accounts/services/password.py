"""Password management services."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from common.exceptions import BadRequest
from common.logging import get_service_logger

logger = get_service_logger("password")


def change_password(user, current_password: str, new_password: str):
    """
    Change user's password after validating current password.
    
    Args:
        user: User instance
        current_password: Current password for verification
        new_password: New password to set
        
    Returns:
        User instance with updated password
        
    Raises:
        BadRequest: If current password is incorrect or new password is invalid
    """
    logger.info("Password change attempt", extra={"user_id": str(user.id)})
    
    # Verify current password
    if not user.check_password(current_password):
        logger.warning("Password change failed - incorrect current password", 
                      extra={"user_id": str(user.id)})
        raise BadRequest(detail="Current password is incorrect")
    
    # Validate new password meets requirements
    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        logger.warning("Password change failed - validation error", 
                      extra={"user_id": str(user.id), "errors": e.messages})
        raise BadRequest(detail="New password does not meet requirements", errors={"new_password": e.messages})
    
    # Check new password is different from current
    if user.check_password(new_password):
        logger.warning("Password change failed - new password same as current", 
                      extra={"user_id": str(user.id)})
        raise BadRequest(detail="New password must be different from current password")
    
    # Set new password
    user.set_password(new_password)
    user.save(update_fields=['password'])
    
    logger.info("Password changed successfully", extra={"user_id": str(user.id)})
    return user

"""Cookie-based JWT authentication for Django REST Framework."""
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model

from .tokens import decode_token

User = get_user_model()


class CookieJWTAuthentication(BaseAuthentication):
    """DRF authentication class that reads JWT from HttpOnly cookies.
    
    Features:
    - Reads access token from secure, HttpOnly cookie
    - Validates JWT signature and expiry
    - Enforces CSRF protection on non-safe methods (POST, PUT, DELETE, etc.)
    - Returns (user, payload) tuple for authenticated requests
    """
    
    def authenticate(self, request):
        """Authenticate request using JWT from cookie.
        
        Returns:
            Tuple of (user, payload) if authentication succeeds
            None if no token present (allows anonymous access)
        
        Raises:
            AuthenticationFailed: Invalid token or user not found
            PermissionDenied: CSRF validation failed
        """
        cookie_name = getattr(settings, "ACCESS_COOKIE_NAME", "access_token")
        token = request.COOKIES.get(cookie_name)
        
        if not token:
            return None
        
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise exceptions.AuthenticationFailed(f"Invalid access token: {exc}")
        
        # Retrieve user from database
        try:
            user = User.objects.get(pk=payload["user_id"])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")
        
        # Enforce CSRF protection for non-safe methods
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            reason = CsrfViewMiddleware(get_response=lambda r: None).process_view(
                request, None, (), {}
            )
            if reason is not None:
                raise exceptions.PermissionDenied(
                    f"CSRF validation failed: {getattr(reason, 'content', reason)}"
                )
        
        return (user, payload)

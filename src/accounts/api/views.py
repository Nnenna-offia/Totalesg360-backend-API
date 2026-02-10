"""Authentication API views."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.middleware import csrf
from django.conf import settings

from common.exceptions import Unauthorized
from common.api import success_response
from accounts.services import auth as auth_services
from accounts.services.signup import signup as signup_service
from accounts.auth.tokens import decode_token
from accounts.selectors.metadata import get_countries_list
from accounts.selectors.user import get_user_memberships_with_roles
from .serializers import LoginSerializer, SignupSerializer


# Cookie configuration helpers
def get_cookie_config(cookie_type: str) -> dict:
    """Get secure cookie configuration based on type."""
    base_config = {
        "httponly": True,
        "secure": True,
        "samesite": "Lax",
    }
    
    if cookie_type == "access":
        base_config.update({
            "key": getattr(settings, "ACCESS_COOKIE_NAME", "access_token"),
            "max_age": getattr(settings, "JWT_ACCESS_LIFETIME_SECONDS", 300),
            "path": "/",
        })
    elif cookie_type == "refresh":
        base_config.update({
            "key": getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token"),
            "max_age": getattr(settings, "JWT_REFRESH_LIFETIME_SECONDS", 7 * 24 * 3600),
            "path": "/",
        })
    elif cookie_type == "csrf":
        base_config.update({
            "key": getattr(settings, "CSRF_COOKIE_NAME", "csrftoken"),
            "httponly": False,  # Frontend must read this
            "path": "/",
        })
    
    return base_config


class LoginView(APIView):
    """Authenticate user and set secure JWT cookies.
    
    POST /auth/login/
    Body: {"email": "user@example.com", "password": "secret"}
    
    Response: 204 No Content with cookies set:
    - access_token (HttpOnly, Secure)
    - refresh_token (HttpOnly, Secure)
    - csrftoken (Secure, readable by JS)
    """
    
    permission_classes = []  # Public endpoint
    authentication_classes = []
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Authenticate user (raises Unauthorized if invalid)
        user = auth_services.authenticate_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )
        
        # Create tokens
        access_token = auth_services.create_access_token(user)
        refresh_token, _ = auth_services.create_refresh_token(
            user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT")
        )
        
        # Get user's memberships with roles and capabilities
        memberships = get_user_memberships_with_roles(user)
        
        # Build response with user info and secure cookies
        response = Response(
            data={
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "memberships": memberships,
            },
            status=status.HTTP_200_OK
        )
        
        # Set access token cookie
        access_config = get_cookie_config("access")
        response.set_cookie(
            key=access_config["key"],
            value=access_token,
            max_age=access_config["max_age"],
            httponly=access_config["httponly"],
            secure=access_config["secure"],
            samesite=access_config["samesite"],
            path=access_config["path"],
        )
        
        # Set refresh token cookie
        refresh_config = get_cookie_config("refresh")
        response.set_cookie(
            key=refresh_config["key"],
            value=refresh_token,
            max_age=refresh_config["max_age"],
            httponly=refresh_config["httponly"],
            secure=refresh_config["secure"],
            samesite=refresh_config["samesite"],
            path=refresh_config["path"],
        )
        
        # Set CSRF token cookie
        csrf_token = csrf.get_token(request)
        csrf_config = get_cookie_config("csrf")
        response.set_cookie(
            key=csrf_config["key"],
            value=csrf_token,
            httponly=csrf_config["httponly"],
            secure=csrf_config["secure"],
            samesite=csrf_config["samesite"],
            path=csrf_config["path"],
        )
        
        return response


class RefreshView(APIView):
    """Rotate refresh token and issue new access token.
    
    POST /auth/refresh/
    
    Reads refresh_token from HttpOnly cookie, validates it, rotates it,
    and sets new access_token and refresh_token cookies.
    
    Response: 204 No Content with updated cookies
    """
    
    permission_classes = []  # Public endpoint
    authentication_classes = []
    
    def post(self, request):
        # Read refresh token from cookie
        refresh_cookie = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
        token = request.COOKIES.get(refresh_cookie)
        
        if not token:
            raise Unauthorized(detail="Missing refresh token")
        
        # Decode and validate
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise Unauthorized(detail=f"Invalid refresh token: {exc}")
        
        # Get user
        from accounts.models import User
        try:
            user = User.objects.get(pk=payload["user_id"])
        except User.DoesNotExist:
            raise Unauthorized(detail="User not found")
        
        # Rotate refresh token (security: revokes old, creates new)
        new_refresh_token, _ = auth_services.rotate_refresh_token(
            old_jti=payload["jti"],
            user=user
        )
        
        # Issue new access token
        new_access_token = auth_services.create_access_token(user)
        
        # Build response with updated cookies
        response = Response(status=status.HTTP_204_NO_CONTENT)
        
        # Set new access token
        access_config = get_cookie_config("access")
        response.set_cookie(
            key=access_config["key"],
            value=new_access_token,
            max_age=access_config["max_age"],
            httponly=access_config["httponly"],
            secure=access_config["secure"],
            samesite=access_config["samesite"],
            path=access_config["path"],
        )
        
        # Set new refresh token
        refresh_config = get_cookie_config("refresh")
        response.set_cookie(
            key=refresh_config["key"],
            value=new_refresh_token,
            max_age=refresh_config["max_age"],
            httponly=refresh_config["httponly"],
            secure=refresh_config["secure"],
            samesite=refresh_config["samesite"],
            path=refresh_config["path"],
        )
        
        return response


class LogoutView(APIView):
    """Logout user by revoking refresh token and clearing cookies.
    
    POST /auth/logout/
    
    Revokes the refresh token server-side and clears all auth cookies.
    
    Response: 204 No Content
    """
    
    # No authentication required - anyone can logout
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        # Try to revoke refresh token if present
        refresh_cookie = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
        token = request.COOKIES.get(refresh_cookie)
        
        if token:
            try:
                payload = decode_token(token)
                auth_services.revoke_refresh_token(payload["jti"])
            except Exception:
                # Token already invalid - continue with cookie clearing
                pass
        
        # Build response and clear all auth cookies
        response = Response(status=status.HTTP_204_NO_CONTENT)
        
        access_cookie = getattr(settings, "ACCESS_COOKIE_NAME", "access_token")
        response.delete_cookie(access_cookie, path="/")
        
        response.delete_cookie(refresh_cookie, path="/")
        
        csrf_cookie = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
        response.delete_cookie(csrf_cookie, path="/")
        
        return response


class CSRFView(APIView):
    """Get CSRF token for frontend bootstrap.
    
    GET /auth/csrf/
    
    Returns CSRF token in cookie. Frontend reads cookie value and sends
    as X-CSRFToken header on non-GET requests.
    
    Response: 204 No Content with csrftoken cookie set
    """
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        # Generate CSRF token and set cookie
        csrf_token = csrf.get_token(request)
        
        response = Response(status=status.HTTP_204_NO_CONTENT)
        
        csrf_config = get_cookie_config("csrf")
        response.set_cookie(
            key=csrf_config["key"],
            value=csrf_token,
            httponly=csrf_config["httponly"],
            secure=csrf_config["secure"],
            samesite=csrf_config["samesite"],
            path=csrf_config["path"],
        )
        
        return response


class SignupView(APIView):
    """Create user account with organization and regulatory framework assignment.
    
    POST /auth/signup/
    Body: {
        "email": "admin@example.com",
        "password": "securepassword",
        "first_name": "John",
        "last_name": "Doe",
        "organization_name": "Acme Corp",
        "sector": "manufacturing",
        "country": "NG",
        "regulatory_coverage": "HYBRID"
    }
    
    Response: 201 Created with user and organization data
    {
        "success": true,
        "data": {
            "user_id": "uuid",
            "email": "admin@example.com",
            "organization_id": "uuid",
            "organization_name": "Acme Corp",
            "sector": "manufacturing",
            "regulatory_coverage": "HYBRID"
        }
    }
    """
    
    permission_classes = []  # Public endpoint
    authentication_classes = []
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call service layer (raises domain exceptions on error)
        result = signup_service(**serializer.validated_data)
        
        return success_response(data=result, status=status.HTTP_201_CREATED)


class CountriesView(APIView):
    """Get list of all countries for dropdowns.
    
    GET /auth/countries/
    
    Returns:
        List of all countries with ISO codes and names.
        
    Response: 200 OK
    {
        "success": true,
        "data": {
            "countries": [
                {"code": "NG", "name": "Nigeria"},
                {"code": "US", "name": "United States"},
                ...
            ]
        }
    }
    """
    
    permission_classes = []  # Public endpoint
    authentication_classes = []
    
    def get(self, request):
        data = {
            "countries": get_countries_list()
        }
        
        return success_response(data=data, status=status.HTTP_200_OK)

"""Authentication API views."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.middleware import csrf
from django.conf import settings

from common.exceptions import Unauthorized
from common.api import success_response, problem_response
from accounts.services import auth as auth_services
from accounts.services.signup import signup as signup_service
from accounts.auth.tokens import decode_token
from accounts.selectors.metadata import get_countries_list
from accounts.selectors.user import (
    get_user_memberships_with_roles,
    get_user_by_email,
    get_latest_email_verification_for_user,
    email_verification_exists_for_user,
)
from .serializers import (
    LoginSerializer,
    SignupSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer,
)
from accounts.utils.otp import create_and_send_otp_for_user, verify_otp
from accounts.utils.password_reset import (
    create_and_send_password_reset_otp,
    verify_password_reset_otp,
)
from accounts.selectors.user import (
    password_reset_exists_for_user,
    get_latest_password_reset_for_user,
)
from accounts.models import User


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
        try:
            user = auth_services.authenticate_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"]
            )
        except Unauthorized as exc:
            email = serializer.validated_data.get("email", "").lower()
            # If the user exists but is not active, return a clear problem detail
            existing_user = get_user_by_email(email)
            if existing_user and not existing_user.is_active:
                return problem_response(
                    {
                        "type": f"{settings.PROBLEM_BASE_URL}/email-not-verified",
                        "title": "Email not verified",
                        "detail": "The email address for this account has not been verified. Please verify your email before logging in.",
                        "code": "email_not_verified",
                    },
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Fallback: invalid credentials
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/invalid-credentials",
                    "title": "Invalid credentials",
                    "detail": str(exc.detail) if getattr(exc, "detail", None) else "Invalid email or password",
                    "code": "invalid_credentials",
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
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

        # Also expose the CSRF token in a response header so JS running on a different
        # origin (e.g., localhost) can read it even when cookies are Secure/HttpOnly
        # (clients may prefer reading header instead of cookies).
        response["X-CSRFToken"] = csrf_token
        response["Access-Control-Expose-Headers"] = ", ".join([
            *(getattr(settings, "CORS_EXPOSE_HEADERS", []) if hasattr(settings, "CORS_EXPOSE_HEADERS") else []),
            "X-CSRFToken",
        ])
        
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



class RequestOTPView(APIView):
    """Request or resend an OTP for an email address."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()

        user = get_user_by_email(email)
        if not user:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/user-not-found",
                    "title": "User not found",
                    "detail": f"No user with email {email} was found",
                    "code": "user_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Determine if this is a resend
        is_resend = email_verification_exists_for_user(user)

        try:
            ev, enqueued = create_and_send_otp_for_user(user, is_resend=is_resend)
        except ValueError as exc:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/otp-rate-limit",
                    "title": "OTP request limit exceeded",
                    "detail": str(exc),
                    "code": "otp_rate_limited",
                },
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/otp-send-failed",
                    "title": "Failed to enqueue OTP email",
                    "detail": "An error occurred while attempting to send the OTP email",
                    "code": "otp_send_failed",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data={"success": True, "enqueued": bool(enqueued)}, status=status.HTTP_202_ACCEPTED)


class VerifyOTPView(APIView):
    """Verify an OTP and activate the user on success."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()
        otp = serializer.validated_data["otp"]

        user = get_user_by_email(email)
        if not user:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/user-not-found",
                    "title": "User not found",
                    "detail": f"No user with email {email} was found",
                    "code": "user_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        ev = get_latest_email_verification_for_user(user)
        if not ev:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/no-otp",
                    "title": "No OTP found",
                    "detail": "No OTP request was found for this user",
                    "code": "no_otp",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if ev.is_expired():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/otp-expired",
                    "title": "OTP expired",
                    "detail": "The provided OTP has expired",
                    "code": "otp_expired",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if verify_otp(otp, ev.hashed_otp):
            ev.mark_verified()
            user.is_active = True
            user.save(update_fields=["is_active"])
            return success_response(data={"user_id": str(user.id)}, status=status.HTTP_200_OK)
        else:
            ev.attempts = (ev.attempts or 0) + 1
            ev.save(update_fields=["attempts"]) 
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/invalid-otp",
                    "title": "Invalid OTP",
                    "detail": "The provided OTP is invalid",
                    "code": "invalid_otp",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class RequestPasswordResetView(APIView):
    """Request or resend a password-reset OTP for an email address."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()

        user = get_user_by_email(email)
        if not user:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/user-not-found",
                    "title": "User not found",
                    "detail": f"No user with email {email} was found",
                    "code": "user_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        is_resend = password_reset_exists_for_user(user)

        try:
            pr, enqueued = create_and_send_password_reset_otp(user, is_resend=is_resend)
        except ValueError as exc:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/otp-rate-limit",
                    "title": "Password reset rate limited",
                    "detail": str(exc),
                    "code": "password_reset_rate_limited",
                },
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/otp-send-failed",
                    "title": "Failed to enqueue password reset email",
                    "detail": "An error occurred while attempting to send the password reset email",
                    "code": "password_reset_send_failed",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data={"success": True, "enqueued": bool(enqueued)}, status=status.HTTP_202_ACCEPTED)


class ResetPasswordView(APIView):
    """Verify a password-reset OTP and set a new password."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        from .serializers import ResetPasswordSerializer

        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = get_user_by_email(email)
        if not user:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/user-not-found",
                    "title": "User not found",
                    "detail": f"No user with email {email} was found",
                    "code": "user_not_found",
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        pr = get_latest_password_reset_for_user(user)
        if not pr:
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/no-otp",
                    "title": "No OTP found",
                    "detail": "No password reset request was found for this user",
                    "code": "no_password_reset",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if pr.is_expired():
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/otp-expired",
                    "title": "OTP expired",
                    "detail": "The provided OTP has expired",
                    "code": "otp_expired",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if verify_password_reset_otp(otp, pr.hashed_otp):
            pr.mark_used()
            user.set_password(new_password)
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
            return success_response(data={"user_id": str(user.id)}, status=status.HTTP_200_OK)
        else:
            pr.attempts = (pr.attempts or 0) + 1
            pr.save(update_fields=["attempts"])
            return problem_response(
                {
                    "type": f"{settings.PROBLEM_BASE_URL}/invalid-otp",
                    "title": "Invalid OTP",
                    "detail": "The provided OTP is invalid",
                    "code": "invalid_otp",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )


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

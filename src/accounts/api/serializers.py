"""Authentication serializers for input validation."""
from rest_framework import serializers
from organizations.models import Organization


class LoginSerializer(serializers.Serializer):
    """Serializer for login endpoint - validates credentials only."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={"input_type": "password"})


class RefreshSerializer(serializers.Serializer):
    """Serializer for token refresh - no body params needed (reads from cookie)."""
    pass


class SignupSerializer(serializers.Serializer):
    """Serializer for signup endpoint - validates input only (no business logic)."""
    
    # User fields
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        min_length=8,
        help_text="Minimum 8 characters"
    )
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    
    # Organization fields
    organization_name = serializers.CharField(required=True, max_length=255)
    sector = serializers.ChoiceField(
        required=True,
        choices=[
            ("manufacturing", "Manufacturing"),
            ("oil_gas", "Oil & Gas"),
            ("finance", "Finance"),
        ]
    )
    country = serializers.CharField(required=True, max_length=2, help_text="ISO 3166-1 alpha-2 country code")
    primary_reporting_focus = serializers.ChoiceField(
        required=True,
        choices=Organization.PrimaryReportingFocus.choices,
        help_text="Primary reporting focus: NIGERIA, INTERNATIONAL, or HYBRID"
    )


class RequestOTPSerializer(serializers.Serializer):
    """Request or resend OTP for an email address."""
    email = serializers.EmailField(required=True)


class VerifyOTPSerializer(serializers.Serializer):
    """Verify provided OTP for email."""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, write_only=True, min_length=4, max_length=8)


class RequestPasswordResetSerializer(serializers.Serializer):
    """Request a password reset code to be sent to email."""
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    """Reset password using OTP code."""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, write_only=True, min_length=4, max_length=8)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"}
    )

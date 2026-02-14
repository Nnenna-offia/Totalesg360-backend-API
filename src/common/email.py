"""Reusable email sending helpers for the project."""
from typing import Iterable, Optional
from django.core.mail import send_mail
from django.conf import settings


def send_email(subject: str, body: str, recipients: Iterable[str], from_email: Optional[str] = None, fail_silently: bool = False) -> int:
    """Send an email to one or more recipients using Django's email backend.

    Returns number of successfully delivered messages as returned by `send_mail`.
    """
    if from_email is None:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)

    # Ensure recipients is a list
    recipients = list(recipients) if not isinstance(recipients, (list, tuple)) else recipients

    return send_mail(subject, body, from_email, recipients, fail_silently=fail_silently)


def make_otp_email_body(otp: str, ttl_seconds: int) -> str:
    minutes = ttl_seconds // 60
    return (
        f"Your verification code is: {otp}\n\n"
        f"It will expire in {minutes} minute(s). If you did not request this, ignore this email."
    )


def make_password_reset_email_body(otp: str, ttl_seconds: int) -> str:
    minutes = ttl_seconds // 60
    return (
        f"You requested a password reset. Your password reset code is: {otp}\n\n"
        f"It will expire in {minutes} minute(s). If you did not request this, please ignore this email or contact support."
    )

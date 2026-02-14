"""OTP helpers: generation, hashing, Redis-based rate limiting, and creation helper."""
import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django_redis import get_redis_connection

from accounts.models import EmailVerification


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    return make_password(otp)


def verify_otp(otp: str, hashed: str) -> bool:
    return check_password(otp, hashed)


def _get_redis():
    try:
        return get_redis_connection("default")
    except Exception:
        # Fallback: try using REDIS_URL via redis-py
        import redis
        return redis.from_url(settings.REDIS_URL)


def _counter_key(prefix: str, identifier: str) -> str:
    return f"otp:{prefix}:{identifier}"


def can_request_otp(identifier: str) -> bool:
    """Checks and increments the hourly request counter. Returns True if allowed."""
    r = _get_redis()
    key = _counter_key("requests", identifier)
    limit = int(getattr(settings, "OTP_MAX_REQUESTS_PER_HOUR", 6))
    ttl = int(getattr(settings, "OTP_TTL_SECONDS", 3600))
    try:
        count = r.incr(key)
        if count == 1:
            r.expire(key, ttl)
        return count <= limit
    except Exception:
        # If Redis unavailable, be permissive (will rely on other checks)
        return True


def can_resend_otp(identifier: str) -> bool:
    """Checks and increments the hourly resend counter. Returns True if allowed."""
    r = _get_redis()
    key = _counter_key("resend", identifier)
    limit = int(getattr(settings, "OTP_MAX_RESEND_PER_HOUR", 5))
    ttl = int(getattr(settings, "OTP_TTL_SECONDS", 3600))
    try:
        count = r.incr(key)
        if count == 1:
            r.expire(key, ttl)
        return count <= limit
    except Exception:
        return True


def create_and_send_otp_for_user(user, *, is_resend: bool = False):
    """Create verification record and enqueue sending OTP via Celery task.

    Returns True on success. Raises ValueError on rate-limit.
    """
    identifier = user.email.lower()

    if not can_request_otp(identifier):
        raise ValueError("OTP request limit reached for this hour")

    if is_resend and not can_resend_otp(identifier):
        raise ValueError("OTP resend limit reached for this hour")

    otp = generate_otp(getattr(settings, "OTP_LENGTH", 6))
    hashed = hash_otp(otp)
    ttl = int(getattr(settings, "OTP_TTL_SECONDS", 3600))
    expires_at = timezone.now() + timedelta(seconds=ttl)

    ev = EmailVerification.objects.create(
        user=user,
        hashed_otp=hashed,
        expires_at=expires_at,
    )

    enqueued = False
    # Enqueue generic email send task from common
    try:
        from common.tasks import send_email_task
        from common.email import make_otp_email_body, send_email

        subject = getattr(settings, "OTP_EMAIL_SUBJECT", "Your verification code")
        body = make_otp_email_body(otp, int(getattr(settings, "OTP_TTL_SECONDS", 3600)))

        # Try to enqueue task
        try:
            send_email_task.delay(user.email, subject, body)
            enqueued = True
        except Exception:
            # Fallback: try synchronous send
            try:
                sent = send_email(subject, body, [user.email])
                enqueued = bool(sent)
            except Exception:
                enqueued = False
    except Exception:
        # If common tasks/email cannot be imported or both send attempts fail,
        # leave enqueued False so caller can surface appropriate info.
        enqueued = False

    return ev, enqueued

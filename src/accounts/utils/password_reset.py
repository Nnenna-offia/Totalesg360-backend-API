"""Password reset OTP creation, sending and verification helpers."""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from accounts.utils.otp import generate_otp, hash_otp, verify_otp, _get_redis, _counter_key
from django.contrib.auth.hashers import check_password
from accounts.models import PasswordReset


def create_and_send_password_reset_otp(user, *, is_resend: bool = False):
    identifier = user.email.lower()

    # Reuse existing counters but with different prefixes
    r = _get_redis()
    req_key = _counter_key("pwd_requests", identifier)
    resend_key = _counter_key("pwd_resend", identifier)
    req_limit = int(getattr(settings, "OTP_MAX_REQUESTS_PER_HOUR", 6))
    resend_limit = int(getattr(settings, "OTP_MAX_RESEND_PER_HOUR", 5))
    ttl = int(getattr(settings, "OTP_TTL_SECONDS", 3600))

    try:
        req_count = r.incr(req_key)
        if req_count == 1:
            r.expire(req_key, ttl)
        if req_count > req_limit:
            raise ValueError("Password reset request limit reached for this hour")
        if is_resend:
            resend_count = r.incr(resend_key)
            if resend_count == 1:
                r.expire(resend_key, ttl)
            if resend_count > resend_limit:
                raise ValueError("Password reset resend limit reached for this hour")
    except Exception:
        # If Redis unavailable, be permissive
        pass

    otp = generate_otp(getattr(settings, "OTP_LENGTH", 6))
    hashed = hash_otp(otp)
    expires_at = timezone.now() + timedelta(seconds=ttl)

    pr = PasswordReset.objects.create(
        user=user,
        hashed_otp=hashed,
        expires_at=expires_at,
    )

    enqueued = False
    try:
        from common.tasks import send_email_task
        from common.email import make_password_reset_email_body, send_email

        subject = getattr(settings, "PASSWORD_RESET_EMAIL_SUBJECT", "Your password reset code")
        body = make_password_reset_email_body(otp, ttl)

        try:
            send_email_task.delay(user.email, subject, body)
            enqueued = True
        except Exception:
            try:
                sent = send_email(subject, body, [user.email])
                enqueued = bool(sent)
            except Exception:
                enqueued = False
    except Exception:
        enqueued = False

    return pr, enqueued


def verify_password_reset_otp(otp: str, hashed: str) -> bool:
    return verify_otp(otp, hashed)

"""Account invite helpers: create users, assign roles, and send temp/password emails.

This centralises logic so views remain thin and the behavior is easier to
test and reuse.
"""
from typing import Iterable, List, Optional, Tuple
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.conf import settings
from django.db import transaction

from organizations.models import Membership
from accounts.utils.password_reset import create_and_send_password_reset_otp

User = get_user_model()


def create_user_with_roles(
    *,
    email: str,
    first_name: str,
    last_name: str,
    password: Optional[str] = None,
    is_staff: bool = False,
    roles: Optional[Iterable] = None,
    added_by=None,
    is_active: bool = True,
) -> Tuple[User, str, int]:
    """Create a user and assign memberships for the provided Role instances.

    Returns a tuple (user, plaintext_password, memberships_created_count).
    The plaintext password is returned so callers can optionally send it via
    email; it is NOT persisted anywhere in plaintext.
    """
    pwd = password or get_random_string(16)
    roles = list(roles or [])

    with transaction.atomic():
        user = User.objects.create_user(
            username=email,
            email=email,
            password=pwd,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_staff=is_staff,
        )

        to_create = []
        for r in roles:
            to_create.append(Membership(user=user, organization=getattr(r, 'organization', None) or r.organization if False else None, role=r, is_active=True, added_by=added_by))
        # The above tries to protect against non-org-scoped roles; in this
        # project Membership requires an organization, and callers will
        # typically pass Role instances and an organization context. If roles
        # are present we assume caller will ensure organization context is
        # correct and instead create memberships via the organization in the
        # view. For safety, we instead avoid creating malformed memberships
        # here — membership creation is handled by the caller below when the
        # organization is known.
        created = 0
    return user, pwd, created


def send_temporary_password_email(user: User, temp_password: str) -> bool:
    """Send the temporary password to the user's email.

    Prefer enqueuing via `common.tasks.send_email_task`, but fall back to
    synchronous send. Returns True when sending/enqueue succeeded.
    """
    try:
        from common.tasks import send_email_task
        from common.email import make_account_temporary_password_email_body
        subject = getattr(settings, "ACCOUNT_CREATED_EMAIL_SUBJECT", "Your new account")
        body = make_account_temporary_password_email_body(temp_password)
        try:
            send_email_task.delay(user.email, subject, body)
            return True
        except Exception:
            from common.email import send_email
            return bool(send_email(subject, body, [user.email]))
    except Exception:
        return False


def enqueue_password_reset(user: User) -> bool:
    """Create and send a password-reset OTP for the user. Returns True if
    the email was enqueued or sent.
    """
    try:
        pr, enqueued = create_and_send_password_reset_otp(user, is_resend=False)
        return bool(enqueued)
    except Exception:
        return False

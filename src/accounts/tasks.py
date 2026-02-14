"""Deprecated: per-app email task.

Email sending has been centralized under `common.tasks.send_email_task`.
This module remains as a compatibility shim and will delegate to the
common task to avoid import errors in older code paths.
"""
from common.tasks import send_email_task


def send_otp_email_task(*args, **kwargs):
    """Compatibility shim that delegates to `common.tasks.send_email_task`.

    Prefer using `common.tasks.send_email_task` directly.
    """
    return send_email_task(*args, **kwargs)

"""Shared Celery tasks for common functionality (email sending, notifications)."""
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True)
def send_email_task(self, recipients, subject, body, from_email=None, fail_silently=False):
    """Send email via Django `send_mail` asynchronously.

    - `recipients` can be a single email or a list.
    - This task is generic and reusable for notifications.
    """
    if isinstance(recipients, (list, tuple)):
        to_list = list(recipients)
    else:
        to_list = [recipients]

    if from_email is None:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)

    # Use Django's send_mail. Let exceptions bubble so Celery can retry if configured.
    return send_mail(subject, body, from_email, to_list, fail_silently=fail_silently)

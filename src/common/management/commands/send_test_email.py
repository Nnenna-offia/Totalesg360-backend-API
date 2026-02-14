from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email using common.email.send_email (sync) or common.tasks.send_email_task (async)"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Recipient email address")
        parser.add_argument(
            "--mode",
            choices=("sync", "async"),
            default="sync",
            help="Use sync send_email (sync) or enqueue Celery task (async)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        mode = options["mode"]

        # Local import to avoid startup import issues
        try:
            from common.email import send_email, make_otp_email_body
            from common.tasks import send_email_task
        except Exception as exc:
            raise CommandError(f"Failed to import common email utilities: {exc}")

        subject = getattr(settings, "OTP_EMAIL_SUBJECT", "Test email from Totalesg360")
        body = make_otp_email_body("123456", int(getattr(settings, "OTP_TTL_SECONDS", 3600)))

        if mode == "sync":
            self.stdout.write("Sending synchronous test email...")
            try:
                count = send_email(subject, body, [email])
                self.stdout.write(self.style.SUCCESS(f"send_email returned: {count}"))
            except Exception as exc:
                raise CommandError(f"send_email failed: {exc}")
        else:
            self.stdout.write("Enqueuing async test email via Celery task...")
            try:
                task = send_email_task.delay([email], subject, body)
                self.stdout.write(self.style.SUCCESS(f"Enqueued task id: {task.id}"))
            except Exception as exc:
                raise CommandError(f"Failed to enqueue send_email_task: {exc}")

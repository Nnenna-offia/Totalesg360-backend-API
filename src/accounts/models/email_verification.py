from django.db import models
from django.conf import settings
from django.utils import timezone


class EmailVerification(models.Model):
    """Stores hashed OTPs for email verification attempts."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verifications")
    hashed_otp = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]
        ordering = ["-created_at"]

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def mark_verified(self):
        self.verified_at = timezone.now()
        self.save(update_fields=["verified_at"])

    def __str__(self):
        return f"EmailVerification(user={self.user_id}, created={self.created_at.isoformat()})"

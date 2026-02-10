"""Refresh token model for JWT rotation and revocation."""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class RefreshToken(models.Model):
    """Server-side allowlist for refresh tokens with rotation support.
    
    Security features:
    - Tracks token usage and rotation via `replaced_by`
    - Enables detection of token reuse attacks
    - Supports IP and user agent tracking for audit
    - Allows per-token and bulk revocation
    """
    
    jti = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="JWT ID - unique identifier for this refresh token"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
        help_text="User who owns this refresh token"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Token expiration timestamp"
    )
    revoked = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether token has been revoked (logout, rotation, or security)"
    )
    replaced_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="JTI of token that replaced this one (for rotation tracking)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address where token was issued"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent string where token was issued"
    )

    class Meta:
        db_table = "accounts_refresh_token"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "revoked"]),
            models.Index(fields=["expires_at"]),
        ]

    @property
    def is_active(self):
        """Check if token is valid for use.
        
        Returns:
            True if token is not revoked and not expired
        """
        return (not self.revoked) and (self.expires_at > timezone.now())

    def __str__(self):
        status = "active" if self.is_active else "revoked/expired"
        return f"RefreshToken({self.jti}) for {self.user.email} - {status}"

# accounts/models/user.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from common.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User model extending AbstractUser and BaseModel.
    Permissions are handled via Membership + Role + Capability.
    """
    email = models.EmailField(unique=True)
    # AbstractUser already provides first_name, last_name, so we override if needed
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # AbstractUser already has is_active, is_staff, is_superuser
    # We keep them for Django admin access

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
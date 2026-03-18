from django.db import models
from common.models import BaseModel


class Scope(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'activities_scope'
        verbose_name = 'Scope'
        verbose_name_plural = 'Scopes'

    def __str__(self):
        return f"{self.name} ({self.code})"

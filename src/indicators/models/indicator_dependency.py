from django.db import models

from common.models import BaseModel


class IndicatorDependency(BaseModel):
    """Defines computational dependency graph between indicators.

    Example:
    - parent_indicator: Scope 1 emissions
    - child_indicator: Diesel consumption
    - relationship_type: conversion
    """

    class RelationshipType(models.TextChoices):
        AGGREGATION = "aggregation", "Aggregation"
        CONVERSION = "conversion", "Conversion"

    parent_indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.CASCADE,
        related_name="indicator_dependencies",
    )
    child_indicator = models.ForeignKey(
        "indicators.Indicator",
        on_delete=models.CASCADE,
        related_name="indicator_dependents",
    )
    relationship_type = models.CharField(
        max_length=20,
        choices=RelationshipType.choices,
        default=RelationshipType.AGGREGATION,
        db_index=True,
    )
    weight = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "indicators_indicatordependency"
        verbose_name = "Indicator Dependency"
        verbose_name_plural = "Indicator Dependencies"
        unique_together = (("parent_indicator", "child_indicator", "relationship_type"),)
        indexes = [
            models.Index(fields=["parent_indicator", "is_active"]),
            models.Index(fields=["child_indicator", "is_active"]),
        ]

    def __str__(self):
        return f"{self.parent_indicator.code} <- {self.child_indicator.code} ({self.relationship_type})"

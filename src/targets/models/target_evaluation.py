from django.db import models
from common.models import BaseModel


class TargetEvaluation(BaseModel):
    """Snapshot of a target's performance at a point in time.

    Created automatically when an IndicatorValue changes so we have a
    full audit trail of how each target was tracking over time.
    """

    class Status(models.TextChoices):
        ON_TRACK = "on_track", "On Track"
        BEHIND = "behind", "Behind"
        ACHIEVED = "achieved", "Achieved"
        NO_DATA = "no_data", "No Data"

    target = models.ForeignKey(
        "targets.TargetGoal",
        on_delete=models.CASCADE,
        related_name="evaluations",
    )
    reporting_period = models.ForeignKey(
        "submissions.ReportingPeriod",
        on_delete=models.CASCADE,
        related_name="target_evaluations",
    )
    actual_value = models.FloatField()
    variance = models.FloatField(
        help_text="actual_value - target_value (negative means behind for INCREASE targets)"
    )
    progress_percent = models.IntegerField(
        default=0, help_text="0-100 progress toward the goal"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, db_index=True
    )

    class Meta:
        db_table = "targets_targetevaluation"
        verbose_name = "Target Evaluation"
        verbose_name_plural = "Target Evaluations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target", "-created_at"]),
            models.Index(fields=["reporting_period", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.target.name} @ {self.created_at:%Y-%m-%d}: {self.status}"

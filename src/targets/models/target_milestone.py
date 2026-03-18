from django.db import models
from common.models import BaseModel


class TargetMilestone(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACHIEVED = 'achieved', 'Achieved'
        AT_RISK = 'at_risk', 'At Risk'

    goal = models.ForeignKey('targets.TargetGoal', on_delete=models.CASCADE, related_name='milestones')
    year = models.IntegerField(db_index=True)
    target_value = models.FloatField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        db_table = 'targets_targetmilestone'
        verbose_name = 'Target Milestone'
        verbose_name_plural = 'Target Milestones'
        ordering = ['year']

    def __str__(self):
        return f"{self.goal.name} • {self.year} → {self.target_value}"

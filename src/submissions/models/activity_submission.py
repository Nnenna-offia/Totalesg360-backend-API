from django.db import models
from common.models import BaseModel
from organizations.models import Organization
from organizations.models.facility import Facility
from submissions.models.reporting_period import ReportingPeriod
from activities.models.activity_type import ActivityType
from django.conf import settings


class ActivitySubmission(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='activity_submissions')
    facility = models.ForeignKey(Facility, null=True, blank=True, on_delete=models.SET_NULL, related_name='activity_submissions')
    activity_type = models.ForeignKey(ActivityType, on_delete=models.PROTECT, related_name='submissions')
    reporting_period = models.ForeignKey(ReportingPeriod, on_delete=models.PROTECT, related_name='activity_submissions')
    value = models.DecimalField(max_digits=18, decimal_places=6)
    unit = models.CharField(max_length=50)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'submissions_activitysubmission'
        verbose_name = 'Activity Submission'
        verbose_name_plural = 'Activity Submissions'

    def __str__(self):
        return f"{self.organization} - {self.activity_type.name} ({self.value} {self.unit})"

from django.db import models
from common.models import BaseModel
from organizations.models import Organization
from organizations.models.facility import Facility
from submissions.models.activity_submission import ActivitySubmission
from emissions.models.emission_factor import EmissionFactor
from activities.models.scope import Scope


class CalculatedEmission(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='calculated_emissions')
    facility = models.ForeignKey(Facility, null=True, blank=True, on_delete=models.SET_NULL)
    activity_submission = models.OneToOneField(ActivitySubmission, on_delete=models.CASCADE, related_name='calculated_emission')
    emission_factor = models.ForeignKey(EmissionFactor, null=True, blank=True, on_delete=models.SET_NULL)
    scope = models.ForeignKey(Scope, on_delete=models.PROTECT)
    emission_value = models.DecimalField(max_digits=20, decimal_places=6)
    reporting_period = models.ForeignKey('submissions.ReportingPeriod', on_delete=models.PROTECT)

    class Meta:
        db_table = 'emissions_calculatedemission'
        verbose_name = 'Calculated Emission'
        verbose_name_plural = 'Calculated Emissions'

    def __str__(self):
        return f"{self.organization} - {self.scope.code}: {self.emission_value}"

from django.db import models
from common.models import BaseModel
from activities.models.activity_type import ActivityType
from django_countries.fields import CountryField


class EmissionFactor(BaseModel):
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE, related_name='emission_factors')
    country = CountryField(blank=True, null=True)
    year = models.PositiveIntegerField()
    factor = models.DecimalField(max_digits=18, decimal_places=8)
    unit = models.CharField(max_length=50, help_text='Unit of factor, e.g. kgCO2e per liter')
    source = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'emissions_emissionfactor'
        verbose_name = 'Emission Factor'
        verbose_name_plural = 'Emission Factors'
        unique_together = [('activity_type', 'country', 'year')]

    def __str__(self):
        country = self.country or 'global'
        return f"{self.activity_type.name} ({country} {self.year}) -> {self.factor} {self.unit}"

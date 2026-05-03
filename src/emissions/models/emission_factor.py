from django.db import models
from common.models import BaseModel
from activities.models.activity_type import ActivityType
from indicators.models import Indicator
from django_countries.fields import CountryField


class EmissionFactor(BaseModel):
    activity_type = models.ForeignKey(
        ActivityType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='emission_factors',
    )
    indicator = models.ForeignKey(
        Indicator,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='emission_factors',
    )
    country = CountryField(blank=True, null=True)
    year = models.PositiveIntegerField()
    factor = models.DecimalField(max_digits=18, decimal_places=8)
    factor_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    unit = models.CharField(max_length=50, help_text='Unit of factor, e.g. kgCO2e per liter')
    unit_input = models.CharField(max_length=50, blank=True, default='')
    unit_output = models.CharField(max_length=50, blank=True, default='')
    source = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'emissions_emissionfactor'
        verbose_name = 'Emission Factor'
        verbose_name_plural = 'Emission Factors'
        unique_together = [('activity_type', 'country', 'year')]

    def __str__(self):
        country = self.country or 'global'
        if self.indicator_id:
            target = self.indicator.code
        elif self.activity_type_id:
            target = self.activity_type.name
        else:
            target = 'unbound-factor'
        value = self.factor_value if self.factor_value is not None else self.factor
        return f"{target} ({country} {self.year}) -> {value} {self.unit}"

    @property
    def effective_factor_value(self):
        return self.factor_value if self.factor_value is not None else self.factor

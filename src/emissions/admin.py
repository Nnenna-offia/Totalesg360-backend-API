from django.contrib import admin
from .models import EmissionFactor, CalculatedEmission


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity_type', 'country', 'year', 'factor', 'unit')
    search_fields = ('activity_type__name', 'country')


@admin.register(CalculatedEmission)
class CalculatedEmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'scope', 'emission_value', 'reporting_period')
    search_fields = ('organization__name',)

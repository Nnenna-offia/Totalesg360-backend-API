from django.contrib import admin
from .models import Indicator, FrameworkIndicator, OrganizationIndicator


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'pillar', 'data_type', 'is_active', 'version')
    search_fields = ('code', 'name')
    list_filter = ('pillar', 'data_type', 'is_active')


@admin.register(FrameworkIndicator)
class FrameworkIndicatorAdmin(admin.ModelAdmin):
    list_display = ('framework', 'indicator', 'is_required', 'display_order')
    list_filter = ('framework', 'is_required')
    search_fields = ('indicator__code', 'indicator__name', 'framework__name')


@admin.register(OrganizationIndicator)
class OrganizationIndicatorAdmin(admin.ModelAdmin):
    list_display = ('organization', 'indicator', 'is_required', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('indicator__code', 'indicator__name', 'organization__name')

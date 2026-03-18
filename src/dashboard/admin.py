from django.contrib import admin
from .models import DashboardMetric, DashboardSnapshot, TargetSnapshot, EmissionSnapshot, IndicatorSnapshot, ComplianceSnapshot


@admin.register(DashboardSnapshot)
class DashboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ('organization', 'snapshot_date', 'source')
    list_filter = ('snapshot_date', 'source')
    search_fields = ('organization__name',)


@admin.register(TargetSnapshot)
class TargetSnapshotAdmin(admin.ModelAdmin):
    list_display = ('organization', 'snapshot_date')
    search_fields = ('organization__name',)


@admin.register(EmissionSnapshot)
class EmissionSnapshotAdmin(admin.ModelAdmin):
    list_display = ('organization', 'snapshot_date')
    search_fields = ('organization__name',)


@admin.register(IndicatorSnapshot)
class IndicatorSnapshotAdmin(admin.ModelAdmin):
    list_display = ('organization', 'snapshot_date')
    search_fields = ('organization__name',)


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ('organization', 'overall_esg_score', 'calculated_at')
    search_fields = ('organization__name',)


@admin.register(ComplianceSnapshot)
class ComplianceSnapshotAdmin(admin.ModelAdmin):
    list_display = ('organization', 'snapshot_date')
    search_fields = ('organization__name',)

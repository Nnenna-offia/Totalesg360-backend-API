from django.contrib import admin
from .models import ReportingPeriod


@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
	list_display = ("organization", "year", "quarter", "status", "opened_at", "locked_at")
	list_filter = ("status", "organization")
	search_fields = ("organization__name",)
    
from .models import DataSubmission


@admin.register(DataSubmission)
class DataSubmissionAdmin(admin.ModelAdmin):
	list_display = ("organization", "indicator", "reporting_period", "facility", "status", "submitted_at")
	list_filter = ("status", "indicator")
	search_fields = ("organization__name", "indicator__code")

from .models import ActivitySubmission


@admin.register(ActivitySubmission)
class ActivitySubmissionAdmin(admin.ModelAdmin):
	list_display = ("organization", "activity_type", "reporting_period", "facility", "value", "unit")
	list_filter = ("activity_type",)
	search_fields = ("organization__name", "activity_type__name")

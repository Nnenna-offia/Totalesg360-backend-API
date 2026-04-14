"""Admin configuration for Reports app."""
from django.contrib import admin
from reports.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin interface for reports."""
    list_display = (
        'organization',
        'report_type',
        'status',
        'file_format',
        'generated_at',
    )
    list_filter = (
        'report_type',
        'status',
        'file_format',
        'generated_at',
    )
    search_fields = (
        'organization__name',
        'id',
    )
    readonly_fields = (
        'id',
        'generated_at',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('Report Info', {
            'fields': ('id', 'organization', 'report_type', 'framework', 'partner_type')
        }),
        ('Status', {
            'fields': ('status', 'generated_by', 'generated_at')
        }),
        ('Export', {
            'fields': ('file_format', 'file_url')
        }),
        ('Data', {
            'fields': ('summary', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-generated_at',)

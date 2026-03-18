from django.contrib import admin
try:
    from .models import ComplianceRecord

    @admin.register(ComplianceRecord)
    class ComplianceRecordAdmin(admin.ModelAdmin):
        list_display = ('id', 'name', 'status', 'created_at')
        search_fields = ('name', 'status')
except Exception:
    # Compliance models may not be present during early development; avoid breaking admin autodiscover
    pass

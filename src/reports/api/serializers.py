"""Serializers for Reports API."""
from rest_framework import serializers
from reports.models import Report


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""
    format_display = serializers.CharField(source="get_file_format_display", read_only=True)
    type_display = serializers.CharField(source="get_report_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    framework_code = serializers.CharField(source="framework.code", read_only=True, allow_null=True)
    
    class Meta:
        model = Report
        fields = [
            "id",
            "organization",
            "report_type",
            "type_display",
            "framework",
            "framework_code",
            "partner_type",
            "status",
            "status_display",
            "file_format",
            "format_display",
            "file_url",
            "summary",
            "generated_at",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "generated_at",
            "created_at",
            "updated_at",
        ]


class GenerateReportRequestSerializer(serializers.Serializer):
    """Serializer for report generation request."""
    report_type = serializers.ChoiceField(
        choices=Report.ReportType.choices,
        required=True,
        help_text="Type of report to generate"
    )
    framework_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Framework ID (required for framework reports)"
    )
    reporting_period_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Reporting period ID (optional)"
    )
    partner_type = serializers.ChoiceField(
        choices=Report.PartnerType.choices,
        default=Report.PartnerType.NONE,
        help_text="Partner type (for partner reports)"
    )
    file_format = serializers.ChoiceField(
        choices=[("json", "JSON"), ("csv", "CSV"), ("html", "HTML"), ("pdf", "PDF")],
        default="json",
        help_text="Export format"
    )


class GenerateReportResponseSerializer(serializers.Serializer):
    """Serializer for report generation response."""
    report_id = serializers.UUIDField()
    status = serializers.CharField()
    report_type = serializers.CharField()
    download_url = serializers.URLField(allow_null=True)
    message = serializers.CharField(allow_null=True)


class ReportListSerializer(serializers.ModelSerializer):
    """Serializer for report list view."""
    type_display = serializers.CharField(source="get_report_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    
    class Meta:
        model = Report
        fields = [
            "id",
            "report_type",
            "type_display",
            "status",
            "status_display",
            "generated_at",
        ]
        read_only_fields = ["id", "generated_at"]

"""Serializers for organization settings API."""
from rest_framework import serializers
from organizations.models import (
    Organization,
    OrganizationSettings,
    OrganizationProfile,
    Department,
    OrganizationFramework
)
from organizations.models import BusinessUnit


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    
    head_name = serializers.CharField(source='head.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Department
        fields = [
            'id',
            'organization',
            'name',
            'code',
            'description',
            'head',
            'head_name',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']


class OrganizationFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationFramework with framework details."""
    
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    framework_code = serializers.CharField(source='framework.code', read_only=True)
    
    class Meta:
        model = OrganizationFramework
        fields = [
            'id',
            'framework',
            'framework_name',
            'framework_code',
            'is_primary',
            'is_enabled',
            'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationSettings model."""
    
    class Meta:
        model = OrganizationSettings
        fields = [
            'id',
            'system_language',
            'timezone',
            'currency',
            'date_format',
            'admin_theme',
            'notifications_enabled',
            'system_update_frequency',
            'security_checks_frequency',
            'export_formats',
            'require_2fa',
            'encrypt_stored_data',
            'encryption_method',
            'local_reporting_frequency',
            'global_reporting_frequency',
            'auto_compliance_enabled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationDetailSerializer(serializers.ModelSerializer):
    """Serializer for Organization with basic details."""
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'registered_name',
            'registration_number',
            'company_size',
            'logo',
            'sector',
            'country',
            'primary_reporting_focus',
            'is_active'
        ]
        read_only_fields = ['id']


class OrganizationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationProfile
        fields = [
            'registered_business_name',
            'cac_registration_number',
            'company_size',
            'logo',
            'operational_locations',
            'fiscal_year_start_month',
            'fiscal_year_end_month',
            'cac_document',
        ]


class BusinessUnitSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = BusinessUnit
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationSettingsDetailSerializer(serializers.Serializer):
    """Return structure split into company, general, security."""

    company = OrganizationProfileSerializer(read_only=True)
    general = OrganizationSettingsSerializer(read_only=True)
    security = serializers.SerializerMethodField()
    departments = DepartmentSerializer(many=True, read_only=True)
    frameworks = OrganizationFrameworkSerializer(many=True, read_only=True)

    def get_security(self, obj):
        # reuse OrganizationSettingsSerializer but expose only security fields
        settings = obj.get('settings')
        if not settings:
            return None
        sec = {
            'security_checks_frequency': settings.security_checks_frequency,
            'require_2fa': settings.require_2fa,
            'encrypt_stored_data': settings.encrypt_stored_data,
            'encryption_method': settings.encryption_method,
            'auto_compliance_enabled': settings.auto_compliance_enabled,
        }
        return sec


class OrganizationSettingsDetailSerializer(serializers.Serializer):
    """Complete serializer for organization settings view."""
    
    organization = OrganizationDetailSerializer(read_only=True)
    settings = OrganizationSettingsSerializer(read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)
    frameworks = OrganizationFrameworkSerializer(many=True, read_only=True)


class GeneralSettingsUpdateSerializer(serializers.Serializer):
    """Serializer for updating general settings."""
    
    system_language = serializers.ChoiceField(
        choices=OrganizationSettings.SystemLanguage.choices,
        required=False
    )
    timezone = serializers.ChoiceField(
        choices=OrganizationSettings.Timezone.choices,
        required=False
    )
    currency = serializers.ChoiceField(
        choices=OrganizationSettings.Currency.choices,
        required=False
    )
    date_format = serializers.ChoiceField(
        choices=OrganizationSettings.DateFormat.choices,
        required=False
    )
    admin_theme = serializers.ChoiceField(
        choices=OrganizationSettings.AdminTheme.choices,
        required=False
    )
    notifications_enabled = serializers.BooleanField(required=False)
    system_update_frequency = serializers.ChoiceField(
        choices=OrganizationSettings.UpdateFrequency.choices,
        required=False
    )
    export_formats = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    local_reporting_frequency = serializers.ChoiceField(
        choices=OrganizationSettings.UpdateFrequency.choices,
        required=False
    )
    global_reporting_frequency = serializers.ChoiceField(
        choices=OrganizationSettings.UpdateFrequency.choices,
        required=False
    )


class SecuritySettingsUpdateSerializer(serializers.Serializer):
    """Serializer for updating security settings."""
    
    security_checks_frequency = serializers.ChoiceField(
        choices=OrganizationSettings.UpdateFrequency.choices,
        required=False
    )
    require_2fa = serializers.BooleanField(required=False)
    encrypt_stored_data = serializers.BooleanField(required=False)
    encryption_method = serializers.ChoiceField(
        choices=OrganizationSettings.EncryptionMethod.choices,
        required=False
    )
    auto_compliance_enabled = serializers.BooleanField(required=False)


# ===================================================================
# Organization Hierarchy Serializers
# ===================================================================

class OrganizationHierarchyNodeSerializer(serializers.ModelSerializer):
    """Single node in organization hierarchy tree."""
    
    organization_type_display = serializers.CharField(
        source='get_organization_type_display',
        read_only=True
    )
    parent_id = serializers.UUIDField(source='parent.id', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'organization_type',
            'organization_type_display',
            'parent_id',
            'parent_name',
            'sector',
            'country',
            'is_active',
        ]
        read_only_fields = fields


class OrganizationTreeSerializer(serializers.Serializer):
    """
    Recursive serializer for organization hierarchy tree.
    Can be nested multiple levels deep.
    """
    
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    organization_type = serializers.CharField(read_only=True)
    organization_type_display = serializers.CharField(read_only=True)
    sector = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    subsidiaries = serializers.SerializerMethodField(read_only=True)
    
    def get_subsidiaries(self, obj):
        """Recursively serialize child organizations."""
        if not isinstance(obj, dict):
            # obj is from selector function (dict-based tree)
            children = obj.get('subsidiaries', [])
        else:
            # obj is Organization instance
            children = obj.get('subsidiaries', [])
        
        return [self.to_representation(child) for child in children]


class CreateSubsidiarySerializer(serializers.Serializer):
    """Serializer for creating subsidiary organizations."""
    
    name = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Organization name"
    )
    sector = serializers.ChoiceField(
        choices=[
            ("manufacturing", "Manufacturing"),
            ("oil_gas", "Oil & Gas"),
            ("finance", "Finance"),
        ],
        required=True
    )
    country = serializers.CharField(
        max_length=2,
        required=True,
        help_text="ISO 3166-1 alpha-2 country code"
    )
    organization_type = serializers.ChoiceField(
        choices=Organization.OrganizationType.choices,
        default=Organization.OrganizationType.SUBSIDIARY,
        required=False
    )
    company_size = serializers.ChoiceField(
        choices=[
            ("small", "Small (1-50 employees)"),
            ("medium", "Medium (51-250 employees)"),
            ("large", "Large (251-1000 employees)"),
            ("enterprise", "Enterprise (1000+ employees)"),
        ],
        required=False,
        allow_null=True
    )
    registered_name = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    primary_reporting_focus = serializers.ChoiceField(
        choices=Organization.PrimaryReportingFocus.choices,
        required=False
    )


class OrganizationStatisticsSerializer(serializers.Serializer):
    """Serializer for organization hierarchy statistics."""
    
    organization_id = serializers.UUIDField(read_only=True)
    total_descendants = serializers.IntegerField(read_only=True)
    direct_children = serializers.IntegerField(read_only=True)
    depth = serializers.IntegerField(read_only=True)
    organization_type = serializers.CharField(read_only=True)
    type_breakdown = serializers.DictField(read_only=True)


class MovleSubsidiarySerializer(serializers.Serializer):
    """Serializer for moving subsidiary to different parent."""
    
    new_parent_id = serializers.UUIDField(
        required=True,
        help_text="ID of new parent organization"
    )

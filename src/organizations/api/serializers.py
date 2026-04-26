"""Serializers for organization settings API."""
import json
from rest_framework import serializers
from submissions.models.reporting_period import ReportingPeriod
from organizations.models import (
    Organization,
    OrganizationSettings,
    OrganizationProfile,
    Department,
    OrganizationFramework,
    OrganizationESGSettings,
    RegulatoryFramework,
)
from organizations.models import BusinessUnit
from organizations.services.hierarchy_validation import validate_hierarchy


class ParentOrganizationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)


class HierarchyValidationMixin:
    def to_internal_value(self, data):
        mutable_data = dict(data)
        if 'organization_type' in mutable_data and 'entity_type' not in mutable_data:
            mutable_data['entity_type'] = mutable_data.pop('organization_type')

        parent_id = mutable_data.pop('parent_id', serializers.empty)
        internal_data = super().to_internal_value(mutable_data)

        if parent_id is not serializers.empty:
            if parent_id in (None, ''):
                internal_data['parent'] = None
            else:
                try:
                    internal_data['parent'] = Organization.objects.get(id=parent_id)
                except Organization.DoesNotExist as exc:
                    raise serializers.ValidationError({'parent_id': 'Parent organization not found'}) from exc

        return internal_data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        entity_type = attrs.get('entity_type', getattr(self.instance, 'entity_type', None))

        if not entity_type:
            entity_type = Organization.EntityType.SUBSIDIARY if parent else Organization.EntityType.GROUP
            attrs['entity_type'] = entity_type

        try:
            validate_hierarchy(parent, entity_type, instance=self.instance)
        except Exception as exc:
            raise serializers.ValidationError({'non_field_errors': [str(exc)]}) from exc
        return attrs


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
    
    framework_id = serializers.UUIDField(source='framework.id', read_only=True)
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    framework_code = serializers.CharField(source='framework.code', read_only=True)
    is_active = serializers.BooleanField(source='is_enabled', read_only=True)
    
    class Meta:
        model = OrganizationFramework
        fields = [
            'id',
            'framework',
            'framework_id',
            'framework_name',
            'framework_code',
            'is_primary',
            'is_active',
            'is_enabled',
            'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']


class FrameworkSelectionItemSerializer(serializers.Serializer):
    framework_id = serializers.UUIDField()
    is_active = serializers.BooleanField()


class OrganizationFrameworkSelectionSerializer(serializers.Serializer):
    frameworks = FrameworkSelectionItemSerializer(many=True)

    def validate_frameworks(self, value):
        if not value:
            raise serializers.ValidationError('At least one framework update is required')

        framework_ids = [item['framework_id'] for item in value]
        if len(framework_ids) != len(set(framework_ids)):
            raise serializers.ValidationError('Duplicate framework_id values are not allowed')
        return value


class FrameworkSelectionOptionSerializer(serializers.Serializer):
    assignment_id = serializers.UUIDField(source='assignment.id', read_only=True, allow_null=True)
    framework_id = serializers.UUIDField(source='framework.id', read_only=True)
    code = serializers.CharField(source='framework.code', read_only=True)
    name = serializers.CharField(source='framework.name', read_only=True)
    jurisdiction = serializers.CharField(source='framework.jurisdiction', read_only=True)
    description = serializers.CharField(source='framework.description', read_only=True)
    sector = serializers.CharField(source='framework.sector', read_only=True)
    priority = serializers.IntegerField(source='framework.priority', read_only=True)
    framework_is_active = serializers.BooleanField(source='framework.is_active', read_only=True)
    is_system = serializers.BooleanField(source='framework.is_system', read_only=True)
    is_assigned = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_enabled = serializers.BooleanField(read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    assigned_at = serializers.DateTimeField(read_only=True, allow_null=True)


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


class OrganizationDetailSerializer(HierarchyValidationMixin, serializers.ModelSerializer):
    """Serializer for Organization with basic details."""
    
    logo = serializers.SerializerMethodField()
    entity_type = serializers.ChoiceField(choices=Organization.EntityType.choices, required=False)
    organization_type = serializers.CharField(source='entity_type', read_only=True)
    parent = serializers.SerializerMethodField(read_only=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
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
            'entity_type',
            'organization_type',
            'parent',
            'parent_id',
            'primary_reporting_focus',
            'is_active'
        ]
        read_only_fields = ['id']

    def get_parent(self, obj):
        if not obj.parent:
            return None
        return ParentOrganizationSerializer(obj.parent).data
    
    def get_logo(self, obj):
        """Return logo URL from organization or fallback to profile logo."""
        if obj.logo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
        
        # Fallback to profile logo if organization logo is null
        try:
            profile = obj.profile
            if profile and profile.logo:
                request = self.context.get('request')
                return request.build_absolute_uri(profile.logo.url) if request else profile.logo.url
        except:
            pass
        
        return None


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationProfile with logo URL fallback."""

    logo = serializers.ImageField(required=False, allow_null=True)
    
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

    def validate_operational_locations(self, value):
        # multipart/form-data can send this field as a JSON string.
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Value must be valid JSON.")

            if not isinstance(parsed, list):
                raise serializers.ValidationError("Value must be a JSON array.")

            return parsed

        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.logo:
            request = self.context.get('request')
            data['logo'] = request.build_absolute_uri(instance.logo.url) if request else instance.logo.url
        else:
            data['logo'] = None

        if instance.cac_document:
            request = self.context.get('request')
            data['cac_document'] = request.build_absolute_uri(instance.cac_document.url) if request else instance.cac_document.url

        return data


class BusinessUnitSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = BusinessUnit
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationSettingsDetailSerializer(serializers.Serializer):
    """
    Comprehensive organization settings response.
    
    Returns all organization data organized by category:
    - organization: Basic org info (name, sector, country, etc.)
    - profile: Company profile data (registered name, CAC number, logo, operational locations)
    - preferences: User/system preferences (language, timezone, theme, notifications)
    - security: Security settings (2FA, encryption, compliance checks)
    - compliance: Compliance-related settings (reporting frequency, auto-compliance)
    - departments: List of active departments
    - frameworks: List of assigned regulatory frameworks
    
    Frontend can fetch this once and update individual sections via PATCH endpoints:
    - PATCH /api/v1/organizations/settings/profile/
    - PATCH /api/v1/organizations/settings/preferences/
    - PATCH /api/v1/organizations/settings/security/
    - PATCH /api/v1/organizations/settings/compliance/
    """
    
    organization = OrganizationDetailSerializer(read_only=True)
    profile = OrganizationProfileSerializer(read_only=True)
    preferences = serializers.SerializerMethodField()
    security = serializers.SerializerMethodField()
    compliance = serializers.SerializerMethodField()
    departments = DepartmentSerializer(many=True, read_only=True)
    frameworks = OrganizationFrameworkSerializer(many=True, read_only=True)
    esg_settings = serializers.SerializerMethodField()

    def get_esg_settings(self, obj):
        settings = obj.get('esg_settings')
        if not settings:
            return None
        return OrganizationESGSettingsSerializer(settings).data
    
    def get_preferences(self, obj):
        """Extract user preference settings."""
        settings = obj.get('settings')
        if not settings:
            return None
        return {
            'system_language': settings.system_language,
            'timezone': settings.timezone,
            'date_format': settings.date_format,
            'admin_theme': settings.admin_theme,
            'notifications_enabled': settings.notifications_enabled,
            'system_update_frequency': settings.system_update_frequency,
            'export_formats': settings.export_formats,
        }
    
    def get_security(self, obj):
        """Extract security settings."""
        settings = obj.get('settings')
        if not settings:
            return None
        return {
            'security_checks_frequency': settings.security_checks_frequency,
            'require_2fa': settings.require_2fa,
            'encrypt_stored_data': settings.encrypt_stored_data,
            'encryption_method': settings.encryption_method,
        }
    
    def get_compliance(self, obj):
        """Extract compliance-related settings."""
        settings = obj.get('settings')
        if not settings:
            return None
        return {
            'local_reporting_frequency': settings.local_reporting_frequency,
            'global_reporting_frequency': settings.global_reporting_frequency,
            'auto_compliance_enabled': settings.auto_compliance_enabled,
            'currency': settings.currency,
        }


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


class OrganizationESGSettingsSerializer(serializers.ModelSerializer):
    reporting_frequency = serializers.CharField()

    class Meta:
        model = OrganizationESGSettings
        fields = [
            'enable_environmental',
            'enable_social',
            'enable_governance',
            'reporting_level',
            'reporting_frequency',
            'fiscal_year_start_month',
            'sector_defaults',
            'updated_at',
        ]
        read_only_fields = ['updated_at']

    def validate_reporting_frequency(self, value):
        normalized = str(value).upper()
        allowed = set(ReportingPeriod.PeriodType.values)
        if normalized not in allowed:
            raise serializers.ValidationError(
                f"Invalid reporting_frequency '{value}'. Must be one of: {', '.join(sorted(allowed))}"
            )
        return normalized

    def validate_fiscal_year_start_month(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError('fiscal_year_start_month must be between 1 and 12')
        return value

    def validate(self, data):
        data = super().validate(data)
        instance = getattr(self, 'instance', None)
        environmental = data.get('enable_environmental', getattr(instance, 'enable_environmental', True))
        social = data.get('enable_social', getattr(instance, 'enable_social', True))
        governance = data.get('enable_governance', getattr(instance, 'enable_governance', True))

        if not any([environmental, social, governance]):
            raise serializers.ValidationError('At least one ESG module must be enabled')

        return data


# ===================================================================
# Organization Hierarchy Serializers
# ===================================================================

class OrganizationHierarchyNodeSerializer(serializers.ModelSerializer):
    """Single node in organization hierarchy tree."""
    
    entity_type = serializers.CharField(read_only=True)
    entity_type_display = serializers.CharField(
        source='get_entity_type_display',
        read_only=True
    )
    organization_type = serializers.CharField(source='entity_type', read_only=True)
    organization_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    parent_id = serializers.UUIDField(source='parent.id', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'entity_type',
            'entity_type_display',
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
    entity_type = serializers.CharField(read_only=True)
    entity_type_display = serializers.CharField(read_only=True)
    organization_type = serializers.CharField(read_only=True)
    organization_type_display = serializers.CharField(read_only=True)
    sector = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    parent = ParentOrganizationSerializer(read_only=True, allow_null=True)
    subsidiaries = serializers.SerializerMethodField(read_only=True)
    children = serializers.SerializerMethodField(read_only=True)
    
    def _get_child_nodes(self, obj):
        """Recursively serialize child organizations."""
        if isinstance(obj, dict):
            child_nodes = obj.get('children') or obj.get('subsidiaries', [])
        else:
            child_nodes = []

        return [self.to_representation(child) for child in child_nodes]

    def get_subsidiaries(self, obj):
        return self._get_child_nodes(obj)

    def get_children(self, obj):
        return self._get_child_nodes(obj)


class CreateSubsidiarySerializer(HierarchyValidationMixin, serializers.Serializer):
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
    entity_type = serializers.ChoiceField(
        choices=Organization.EntityType.choices,
        default=Organization.EntityType.SUBSIDIARY,
        required=False
    )
    organization_type = serializers.ChoiceField(
        choices=Organization.EntityType.choices,
        write_only=True,
        required=False
    )
    parent_id = serializers.UUIDField(required=False, allow_null=True)
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
    hierarchy_depth = serializers.IntegerField(read_only=True)
    entity_type = serializers.CharField(read_only=True)
    organization_type = serializers.CharField(read_only=True)
    type_breakdown = serializers.DictField(read_only=True)


class MovleSubsidiarySerializer(serializers.Serializer):
    """Serializer for moving subsidiary to different parent."""
    
    new_parent_id = serializers.UUIDField(
        required=True,
        help_text="ID of new parent organization"
    )

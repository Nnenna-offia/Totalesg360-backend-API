from django.contrib import admin
from .models import (
    Organization,
    OrganizationSettings,
    Department,
    Facility,
    Membership
)
from .models import OrganizationProfile, BusinessUnit


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'registered_name', 'sector', 'country', 'company_size', 'is_active', 'created_at')
    list_filter = ('sector', 'company_size', 'is_active', 'country')
    search_fields = ('name', 'registered_name', 'registration_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'registered_name', 'registration_number', 'logo')}),
        ('Organization Details', {'fields': ('sector', 'country', 'company_size', 'primary_reporting_focus')}),
        ('Configuration', {'fields': ('settings',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = ('organization', 'system_language', 'timezone', 'currency', 'require_2fa', 'created_at')
    list_filter = ('system_language', 'timezone', 'currency', 'require_2fa', 'encrypt_stored_data')
    search_fields = ('organization__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('organization',)}),
        ('General Settings', {
            'fields': (
                'system_language',
                'timezone',
                'currency',
                'date_format',
                'admin_theme',
                'notifications_enabled',
                'system_update_frequency',
                'export_formats'
            )
        }),
        ('Security Settings', {
            'fields': (
                'security_checks_frequency',
                'require_2fa',
                'encrypt_stored_data',
                'encryption_method'
            )
        }),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('organization', 'name', 'code')}),
        ('Details', {'fields': ('description',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )



@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'facility_type', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'facility_type', 'organization')
    search_fields = ('name', 'location', 'organization__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('organization', 'name', 'facility_type', 'location')}),
        ('Additional Data', {'fields': ('metadata',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'facility', 'is_active', 'joined_at', 'added_by')
    list_filter = ('is_active', 'role', 'organization', 'joined_at')
    search_fields = ('user__email', 'user__username', 'organization__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'joined_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'organization', 'role')}),
        ('Scope', {'fields': ('facility', 'scope')}),
        ('Status & Audit', {'fields': ('is_active', 'joined_at', 'added_by')}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ('organization', 'registered_business_name', 'cac_registration_number', 'company_size', 'created_at')
    search_fields = ('organization__name', 'registered_business_name', 'cac_registration_number')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_at')
    search_fields = ('name', 'organization__name')
    readonly_fields = ('id', 'created_at', 'updated_at')

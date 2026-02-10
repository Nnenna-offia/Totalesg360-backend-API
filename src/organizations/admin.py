from django.contrib import admin
from .models import Organization, Facility, Membership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'country', 'is_active', 'created_at')
    list_filter = ('sector', 'is_active', 'country')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'sector', 'country')}),
        ('Configuration', {'fields': ('settings',)}),
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

from django.contrib import admin
from .models import Role, Capability, RoleCapability


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_system', 'created_at')
    list_filter = ('is_system',)
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('code', 'name', 'description')}),
        ('System', {'fields': ('is_system',)}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('code', 'name', 'description')}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(RoleCapability)
class RoleCapabilityAdmin(admin.ModelAdmin):
    list_display = ('role', 'capability', 'created_at')
    list_filter = ('role',)
    search_fields = ('role__name', 'capability__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('role', 'capability')}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )

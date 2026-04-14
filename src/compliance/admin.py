from django.contrib import admin
from django.utils.html import format_html
from compliance.models import (
    FrameworkRequirement,
    IndicatorFrameworkMapping,
    FrameworkReadiness,
    ComplianceGapPriority,
    ComplianceRecommendation,
)

try:
    from .models import ComplianceRecord

    @admin.register(ComplianceRecord)
    class ComplianceRecordAdmin(admin.ModelAdmin):
        list_display = ('id', 'name', 'status', 'created_at')
        search_fields = ('name', 'status')
except Exception:
    # Compliance models may not be present during early development; avoid breaking admin autodiscover
    pass


@admin.register(FrameworkRequirement)
class FrameworkRequirementAdmin(admin.ModelAdmin):
    """Admin for Framework Requirements."""
    
    list_display = (
        'code', 'framework', 'pillar', 'title_short', 'is_mandatory', 'status'
    )
    list_filter = ('framework', 'pillar', 'is_mandatory', 'status')
    search_fields = ('code', 'title', 'description')
    ordering = ('framework', 'pillar', 'code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Framework & Identification', {
            'fields': ('framework', 'code', 'title', 'version')
        }),
        ('Content', {
            'fields': ('description', 'pillar', 'is_mandatory', 'status')
        }),
        ('Metadata', {
            'fields': ('priority', 'guidance_url', 'created_at', 'updated_at')
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:50]
    title_short.short_description = 'Title'


@admin.register(IndicatorFrameworkMapping)
class IndicatorFrameworkMappingAdmin(admin.ModelAdmin):
    """Admin for Indicator-Framework Mappings."""
    
    list_display = (
        'indicator_code', 'requirement_code', 'framework_code', 
        'mapping_type', 'is_primary', 'coverage_percent', 'is_active'
    )
    list_filter = (
        ('framework', admin.RelatedOnlyFieldListFilter),
        ('requirement__pillar', admin.FieldListFilter),
        'mapping_type',
        'is_primary',
        'is_active'
    )
    search_fields = (
        'indicator__code', 'requirement__code', 'framework__code',
        'indicator__name', 'requirement__title'
    )
    ordering = ('-is_primary', 'framework', 'requirement__code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Mapping', {
            'fields': ('indicator', 'framework', 'requirement')
        }),
        ('Mapping Details', {
            'fields': (
                'mapping_type', 'is_primary', 'coverage_percent',
                'coverage_status_display'
            )
        }),
        ('Justification', {
            'fields': ('rationale', 'notes'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def indicator_code(self, obj):
        return obj.indicator.code
    indicator_code.short_description = 'Indicator'
    
    def requirement_code(self, obj):
        return f"{obj.requirement.code} - {obj.requirement.title[:30]}"
    requirement_code.short_description = 'Requirement'
    
    def framework_code(self, obj):
        return obj.framework.code
    framework_code.short_description = 'Framework'
    
    def coverage_status_display(self, obj):
        status_colors = {
            'full': 'green',
            'substantial': 'orange',
            'partial': 'gold',
            'minimal': 'red'
        }
        status = obj.get_coverage_status()
        return f"<span style='background-color: {status_colors.get(status, 'grey')}; padding: 3px 10px; border-radius: 3px; color: white;'>{status.upper()}</span>"
    coverage_status_display.short_description = 'Coverage Status'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['indicator', 'framework', 'requirement']
        return self.readonly_fields


@admin.register(FrameworkReadiness)
class FrameworkReadinessAdmin(admin.ModelAdmin):
    """Admin for Framework Readiness Scores."""
    
    list_display = (
        'organization_name', 'framework_code', 'readiness_score_display',
        'coverage_percent', 'risk_level_badge', 'is_current'
    )
    list_filter = (
        ('organization', admin.RelatedOnlyFieldListFilter),
        ('framework', admin.RelatedOnlyFieldListFilter),
        'risk_level',
        'is_current',
    )
    search_fields = (
        'organization__name', 'framework__code', 'framework__name'
    )
    ordering = ('-readiness_score', '-calculated_at')
    readonly_fields = ('calculated_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Organization & Framework', {
            'fields': ('organization', 'framework', 'reporting_period')
        }),
        ('Coverage Metrics', {
            'fields': (
                'total_requirements', 'covered_requirements', 'coverage_percent',
                'mandatory_requirements', 'mandatory_covered', 'mandatory_coverage_percent'
            )
        }),
        ('Readiness Assessment', {
            'fields': ('readiness_score', 'risk_level', 'is_current')
        }),
        ('Timestamps', {
            'fields': ('calculated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def organization_name(self, obj):
        return obj.organization.name
    organization_name.short_description = 'Organization'
    
    def framework_code(self, obj):
        return f"{obj.framework.code} - {obj.framework.name}"
    framework_code.short_description = 'Framework'
    
    def readiness_score_display(self, obj):
        color = 'green' if obj.readiness_score >= 80 else 'orange' if obj.readiness_score >= 50 else 'red'
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.readiness_score
        )
    readiness_score_display.short_description = 'Readiness Score'
    
    def risk_level_badge(self, obj):
        colors = {'low': 'green', 'medium': 'orange', 'high': 'red'}
        color = colors.get(obj.risk_level, 'grey')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_risk_level_display()
        )
    risk_level_badge.short_description = 'Risk Level'


@admin.register(ComplianceGapPriority)
class ComplianceGapPriorityAdmin(admin.ModelAdmin):
    """Admin for Compliance Gap Priorities."""
    
    list_display = (
        'organization_name', 'requirement_code', 'priority_badge',
        'priority_score', 'impact_category', 'is_active'
    )
    list_filter = (
        ('organization', admin.RelatedOnlyFieldListFilter),
        ('framework', admin.RelatedOnlyFieldListFilter),
        'priority_level',
        'impact_category',
        'is_active',
    )
    search_fields = (
        'organization__name', 'framework__code',
        'requirement__code', 'requirement__title'
    )
    ordering = ('-priority_score', 'priority_level')
    readonly_fields = ('priority_score', 'last_assessed_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Gap Identification', {
            'fields': ('organization', 'framework', 'requirement')
        }),
        ('Priority Assessment', {
            'fields': (
                'mandatory_weight', 'framework_weight', 'pillar_weight',
                'coverage_impact_weight', 'priority_score', 'priority_level'
            )
        }),
        ('Gap Context', {
            'fields': (
                'impact_category', 'gap_description', 'efforts_to_close',
                'estimated_effort_days'
            )
        }),
        ('Tracking', {
            'fields': ('is_active', 'internal_notes', 'last_assessed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def organization_name(self, obj):
        return obj.organization.name
    organization_name.short_description = 'Organization'
    
    def requirement_code(self, obj):
        return f"{obj.requirement.code} - {obj.requirement.title[:40]}"
    requirement_code.short_description = 'Requirement'
    
    def priority_badge(self, obj):
        colors = {'high': 'red', 'medium': 'orange', 'low': 'green'}
        color = colors.get(obj.priority_level, 'grey')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; color: white; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_level_display()
        )
    priority_badge.short_description = 'Priority'


@admin.register(ComplianceRecommendation)
class ComplianceRecommendationAdmin(admin.ModelAdmin):
    """Admin for Compliance Recommendations."""
    
    list_display = (
        'organization_name', 'requirement_code', 'recommendation_type',
        'priority_badge', 'impact_display', 'status_badge'
    )
    list_filter = (
        ('organization', admin.RelatedOnlyFieldListFilter),
        ('framework', admin.RelatedOnlyFieldListFilter),
        'recommendation_type',
        'priority',
        'status',
    )
    search_fields = (
        'organization__name', 'framework__code',
        'requirement__code', 'title', 'description'
    )
    ordering = ('-priority', '-impact_score', 'status')
    readonly_fields = ('generated_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Context', {
            'fields': ('organization', 'framework', 'requirement')
        }),
        ('Recommendation Details', {
            'fields': (
                'title', 'description', 'recommendation_type',
                'actionable_steps'
            )
        }),
        ('Impact & Priority', {
            'fields': ('impact_score', 'priority', 'estimated_effort_days')
        }),
        ('Implementation', {
            'fields': (
                'status', 'started_at', 'completed_at',
                'required_resources', 'dependencies'
            ),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('internal_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('generated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def organization_name(self, obj):
        return obj.organization.name
    organization_name.short_description = 'Organization'
    
    def requirement_code(self, obj):
        return f"{obj.requirement.code}"
    requirement_code.short_description = 'Requirement'
    
    def priority_badge(self, obj):
        colors = {'high': 'red', 'medium': 'orange', 'low': 'green'}
        color = colors.get(obj.priority, 'grey')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def impact_display(self, obj):
        return f"{obj.impact_score}/10"
    impact_display.short_description = 'Impact'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'grey',
            'in_progress': 'blue',
            'completed': 'green',
            'deferred': 'orange'
        }
        color = colors.get(obj.status, 'grey')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['mark_in_progress', 'mark_completed']
    
    def mark_in_progress(self, request, queryset):
        for rec in queryset:
            rec.mark_in_progress()
        self.message_user(request, f"{queryset.count()} recommendations marked in progress.")
    mark_in_progress.short_description = "Mark selected as In Progress"
    
    def mark_completed(self, request, queryset):
        for rec in queryset:
            rec.mark_completed()
        self.message_user(request, f"{queryset.count()} recommendations marked completed.")
    mark_completed.short_description = "Mark selected as Completed"

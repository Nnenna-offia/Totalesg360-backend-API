"""ESG Scoring Admin Configuration."""
from django.contrib import admin
from django.utils.html import format_html

from esg_scoring.models import IndicatorScore, PillarScore, ESGScore


@admin.register(IndicatorScore)
class IndicatorScoreAdmin(admin.ModelAdmin):
    """Admin interface for IndicatorScore."""
    
    list_display = ('organization', 'indicator', 'reporting_period', 'score_display', 'status', 'progress_display', 'calculated_at')
    list_filter = ('status', 'reporting_period', 'organization', 'is_manual')
    search_fields = ('organization__name', 'indicator__name')
    readonly_fields = ('score', 'progress', 'status', 'calculated_at', 'created_at', 'updated_at', 'id')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'indicator', 'reporting_period')
        }),
        ('Score Data', {
            'fields': ('value', 'target', 'baseline', 'score', 'progress', 'status')
        }),
        ('Metadata', {
            'fields': ('calculation_method', 'is_manual', 'note', 'calculated_at', 'created_at', 'updated_at')
        }),
    )
    
    def score_display(self, obj):
        """Display score with color coding."""
        if obj.score >= 75:
            color = 'green'
        elif obj.score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            obj.score
        )
    score_display.short_description = 'Score'
    
    def progress_display(self, obj):
        """Display progress percentage with bar."""
        return f"{obj.progress:.1f}%"
    progress_display.short_description = 'Progress'


@admin.register(PillarScore)
class PillarScoreAdmin(admin.ModelAdmin):
    """Admin interface for PillarScore."""
    
    list_display = ('organization', 'pillar', 'reporting_period', 'score_display', 'indicator_count', 'health_status_display', 'calculated_at')
    list_filter = ('pillar', 'reporting_period', 'organization')
    search_fields = ('organization__name',)
    readonly_fields = ('score', 'calculated_at', 'created_at', 'updated_at', 'id')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'pillar', 'reporting_period')
        }),
        ('Score Data', {
            'fields': ('score', 'indicator_count', 'on_track_count', 'at_risk_count')
        }),
        ('Metadata', {
            'fields': ('is_dirty', 'calculated_at', 'created_at', 'updated_at')
        }),
    )
    
    def score_display(self, obj):
        """Display score with color coding."""
        if obj.score >= 75:
            color = 'green'
        elif obj.score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            obj.score
        )
    score_display.short_description = 'Score'
    
    def health_status_display(self, obj):
        """Display health status."""
        status = obj.get_health_status()
        colors = {
            'Excellent': 'green',
            'Good': 'lightgreen',
            'Fair': 'orange',
            'Poor': 'red',
        }
        color = colors.get(status, 'gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; color: white; font-weight: bold;">{}</span>',
            color,
            status
        )
    health_status_display.short_description = 'Health Status'


@admin.register(ESGScore)
class ESGScoreAdmin(admin.ModelAdmin):
    """Admin interface for ESGScore."""
    
    list_display = ('organization', 'reporting_period', 'overall_score_display', 'e_score_display', 's_score_display', 'g_score_display', 'consolidation_display', 'calculated_at')
    list_filter = ('reporting_period', 'organization', 'is_consolidated')
    search_fields = ('organization__name',)
    readonly_fields = ('overall_score', 'calculated_at', 'created_at', 'updated_at', 'id')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'reporting_period')
        }),
        ('Pillar Scores', {
            'fields': ('environmental_score', 'social_score', 'governance_score', 'overall_score')
        }),
        ('Weights', {
            'fields': ('environmental_weight', 'social_weight', 'governance_weight'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_consolidated', 'is_dirty', 'calculated_at', 'created_at', 'updated_at')
        }),
    )
    
    def overall_score_display(self, obj):
        """Display overall score with color coding."""
        if obj.overall_score >= 75:
            color = 'green'
        elif obj.overall_score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            obj.overall_score
        )
    overall_score_display.short_description = 'Overall Score'
    
    def e_score_display(self, obj):
        """Display environmental score."""
        return f"{obj.environmental_score:.1f}"
    e_score_display.short_description = 'E'
    
    def s_score_display(self, obj):
        """Display social score."""
        return f"{obj.social_score:.1f}"
    s_score_display.short_description = 'S'
    
    def g_score_display(self, obj):
        """Display governance score."""
        return f"{obj.governance_score:.1f}"
    g_score_display.short_description = 'G'
    
    def consolidation_display(self, obj):
        """Display consolidation status."""
        if obj.is_consolidated:
            return format_html(
                '<span style="background-color: blue; padding: 3px 8px; border-radius: 3px; color: white; font-weight: bold;">Group</span>'
            )
        return format_html(
            '<span style="background-color: gray; padding: 3px 8px; border-radius: 3px; color: white; font-weight: bold;">Org</span>'
        )
    consolidation_display.short_description = 'Type'

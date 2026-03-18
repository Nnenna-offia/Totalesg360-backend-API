from django.contrib import admin
from .models import TargetGoal, TargetMilestone


@admin.register(TargetGoal)
class TargetGoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'organization', 'indicator', 'status')
    list_filter = ('status',)


@admin.register(TargetMilestone)
class TargetMilestoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'goal', 'year', 'target_value', 'status')
    list_filter = ('status', 'year')

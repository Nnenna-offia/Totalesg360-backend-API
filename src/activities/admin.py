from django.contrib import admin
from activities.models.scope import Scope
from activities.models.activity_type import ActivityType


@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name', 'code')


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'scope', 'is_active')
    search_fields = ('name',)

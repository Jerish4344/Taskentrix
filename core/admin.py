from django.contrib import admin
from .models import (
    Organization, Outlet, Team, Permission, Role,
    UserProfile, ActivityLog,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'code', 'is_active')
    list_filter = ('organization', 'is_active')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'color', 'is_active')
    list_filter = ('organization',)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'module')
    list_filter = ('module',)
    search_fields = ('name', 'codename')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_at')
    list_filter = ('organization',)
    filter_horizontal = ('permissions',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'outlet', 'team', 'employee_id')
    list_filter = ('organization', 'role', 'outlet', 'team')
    search_fields = ('user__username', 'user__email', 'employee_id')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'entity_type', 'organization', 'created_at')
    list_filter = ('action', 'entity_type', 'organization')
    date_hierarchy = 'created_at'

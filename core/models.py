"""
Core models: Organization, Outlet, Team, Permission, Role, UserProfile, ActivityLog, Notification
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    logo = models.CharField(max_length=10, default="🏢")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class Outlet(models.Model):
    """Store/Branch under an organization (like ATTAKULANGARA STORE, ATTINGAL SM)."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="outlets")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.code})"


class Team(models.Model):
    """Team within an organization (MAINTENANCE, IT Department, GROCERY TEAM, etc.)."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#6366f1")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.code})"


class Permission(models.Model):
    MODULE_CHOICES = [
        ("dashboard", "Dashboard"),
        ("projects", "Projects"),
        ("tasks", "Task Management"),
        ("issues", "Issues"),
        ("templates", "Template Library"),
        ("reports", "Reports"),
        ("forms", "Forms"),
        ("users", "User Management"),
        ("roles", "Role Management"),
        ("outlets", "Outlet Management"),
        ("ai", "AI Assistant"),
        ("settings", "Settings"),
    ]

    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)

    class Meta:
        ordering = ["module", "name"]
        indexes = [
            models.Index(fields=["codename"]),
            models.Index(fields=["module"]),
        ]

    def __str__(self):
        return f"{self.module} - {self.name}"


class Role(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.code})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="members")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    employee_id = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    avatar_color = models.CharField(max_length=7, default="#6366f1")
    points = models.IntegerField(default=0)
    stylehr_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["organization", "role"]),
            models.Index(fields=["organization", "outlet"]),
            models.Index(fields=["organization", "team"]),
            models.Index(fields=["employee_id"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.organization.code})"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def initials(self):
        name = self.full_name
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:2].upper()

    def has_perm(self, codename):
        if not self.role:
            return False
        return self.role.permissions.filter(codename=codename).exists()


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
        ("status_changed", "Status Changed"),
        ("assigned", "Assigned"),
        ("commented", "Commented"),
        ("login", "Login"),
        ("logout", "Logout"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField(null=True, blank=True)
    entity_name = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["organization", "action"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.entity_type}"


"""Issues app models."""
from django.db import models
from django.utils import timezone
from core.models import Organization, Outlet, Team, UserProfile


class Issue(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("resolved", "Resolved"),
        ("ignored", "Ignore"),
        ("closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("none", "None"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="issues")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="none")
    assigned_to = models.ManyToManyField(UserProfile, blank=True, related_name="assigned_issues")
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="created_issues")
    start_date = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    tags = models.CharField(max_length=500, blank=True)
    is_trashed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "priority"]),
            models.Index(fields=["organization", "outlet"]),
            models.Index(fields=["organization", "team"]),
            models.Index(fields=["organization", "is_trashed"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

    @property
    def priority_color(self):
        colors = {
            "critical": "#ef4444", "high": "#f97316",
            "medium": "#eab308", "low": "#22c55e", "none": "#6b7280",
        }
        return colors.get(self.priority, "#6b7280")

    @property
    def status_color(self):
        colors = {
            "open": "#f97316", "resolved": "#22c55e",
            "ignored": "#6b7280", "closed": "#3b82f6",
        }
        return colors.get(self.status, "#6b7280")


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment on {self.issue.title}"

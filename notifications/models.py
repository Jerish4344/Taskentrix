"""Notifications app models."""
from django.db import models
from core.models import Organization, UserProfile


class Notification(models.Model):
    TYPE_CHOICES = [
        ("task_assigned", "Task Assigned"),
        ("task_completed", "Task Completed"),
        ("task_overdue", "Task Overdue"),
        ("task_comment", "Task Comment"),
        ("issue_created", "Issue Created"),
        ("issue_resolved", "Issue Resolved"),
        ("project_update", "Project Update"),
        ("form_response", "Form Response"),
        ("ai_suggestion", "AI Suggestion"),
        ("reminder", "Reminder"),
        ("system", "System"),
    ]

    PRIORITY_CHOICES = [
        ("high", "High"),
        ("normal", "Normal"),
        ("low", "Low"),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="notifications")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="notifications", null=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="system")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

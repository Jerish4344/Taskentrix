"""Reports app models: Saved/generated reports."""
from django.db import models
from core.models import Organization, UserProfile


class SavedReport(models.Model):
    """User-saved report configurations."""
    REPORT_TYPE_CHOICES = [
        ("outlet_tasks", "All Outlets Tasks Report"),
        ("outlet_issues", "All Outlets Issues Report"),
        ("employee_tasks", "Employee & Outlet wise Tasks with Status"),
        ("employee_issues", "Employee & Outlet wise Issues with Status"),
        ("backlog", "Backlog Report"),
        ("monthly_points", "Month On Month Userwise Points"),
        ("outlet_checklist", "Outlet-wise Checklist Points Report"),
        ("employee_taskwise", "Employee wise - Task wise Report"),
        ("task_submission", "Task Submission Report Outlet-wise"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="saved_reports")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="saved_reports")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ReportCache(models.Model):
    """Cached report data for performance."""
    report_key = models.CharField(max_length=255, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["report_key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return self.report_key

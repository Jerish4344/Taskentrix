"""
Projects app models: Project with overview, board, and list views.
"""
from django.db import models
from django.utils import timezone
from core.models import Organization, Outlet, UserProfile


class ProjectTag(models.Model):
    """Tags for categorizing projects."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="project_tags")
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#6366f1")

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="projects")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    tags = models.ManyToManyField(ProjectTag, blank=True, related_name="projects")
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="created_projects")
    members = models.ManyToManyField(UserProfile, blank=True, related_name="member_projects")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "outlet"]),
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name

    @property
    def total_tasks(self):
        return self.tasks.count()

    @property
    def completed_tasks(self):
        return self.tasks.filter(status="completed").count()

    @property
    def ongoing_tasks(self):
        return self.tasks.filter(status__in=["in_progress", "todo"]).count()

    @property
    def overdue_tasks(self):
        today = timezone.now().date()
        return self.tasks.filter(due_date__lt=today).exclude(status="completed").count()

    @property
    def progress_percent(self):
        total = self.total_tasks
        if total == 0:
            return 0
        return int((self.completed_tasks / total) * 100)

    @property
    def single_task_count(self):
        return self.tasks.filter(parent__isnull=True, task_type="single").count()

    @property
    def group_task_count(self):
        return self.tasks.filter(parent__isnull=True, task_type="group").count()


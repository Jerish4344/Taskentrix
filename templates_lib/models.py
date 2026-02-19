"""Template Library models: Task and Project templates."""
from django.db import models
from core.models import Organization, UserProfile


class TemplateCategory(models.Model):
    """Categories for templates (Stock check, Audit, Cleaning, etc.)."""
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#22c55e")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Template Categories"

    def __str__(self):
        return self.name


class TemplateIndustry(models.Model):
    """Industry tags for templates (Catering, Construction, Logistics, etc.)."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Template Industries"

    def __str__(self):
        return self.name


class TaskTemplate(models.Model):
    """Reusable task templates with subtasks and steps."""
    PRIORITY_CHOICES = [
        ("critical", "Critical"), ("high", "High"),
        ("medium", "Medium"), ("low", "Low"), ("none", "None"),
    ]
    RECURRENCE_CHOICES = [
        ("none", "None"), ("daily", "Daily"), ("weekly", "Weekly"),
        ("monthly", "Monthly"), ("custom", "Custom"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="task_templates")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="none")
    start_time = models.TimeField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default="none")
    recurrence_details = models.JSONField(default=dict, blank=True)
    category = models.ForeignKey(TemplateCategory, on_delete=models.SET_NULL, null=True, blank=True)
    industries = models.ManyToManyField(TemplateIndustry, blank=True, related_name="templates")
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.name

    @property
    def subtask_count(self):
        return self.subtasks.count()


class TaskTemplateSubtask(models.Model):
    """Subtasks within a task template."""
    template = models.ForeignKey(TaskTemplate, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ProjectTemplate(models.Model):
    """Reusable project templates."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="project_templates")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

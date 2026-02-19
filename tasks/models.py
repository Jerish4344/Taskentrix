"""Tasks app models: Task, SubTask, TaskStep, TaskComment, TaskAttachment."""
from django.db import models
from django.utils import timezone
from core.models import Organization, Outlet, Team, UserProfile
from projects.models import Project


class TaskCategory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="task_categories")
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#6366f1")
    icon = models.CharField(max_length=10, default="\ud83d\udcc1")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["organization", "name"]
        verbose_name_plural = "Task Categories"

    def __str__(self):
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("none", "None"),
    ]

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("review", "In Review"),
        ("completed", "Completed"),
        ("on_hold", "On Hold"),
        ("scheduled", "Scheduled"),
        ("overdue", "Overdue"),
    ]

    TYPE_CHOICES = [
        ("single", "Single Task"),
        ("group", "Group Task"),
    ]

    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("custom", "Custom"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="tasks")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="subtasks")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    sop_content = models.TextField(blank=True, help_text="Standard Operating Procedure / rich description")
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="single")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="none")
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    assigned_to = models.ManyToManyField(UserProfile, blank=True, related_name="assigned_tasks")
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="created_tasks")
    start_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    points = models.IntegerField(default=0)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default="none")
    recurrence_details = models.JSONField(default=dict, blank=True)
    needs_approval = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    save_as_template = models.BooleanField(default=False)
    ai_summary = models.TextField(blank=True)
    ai_priority_suggestion = models.CharField(max_length=20, blank=True)
    ai_delay_prediction = models.JSONField(default=dict, blank=True)
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
            models.Index(fields=["organization", "project"]),
            models.Index(fields=["organization", "due_date"]),
            models.Index(fields=["organization", "category"]),
            models.Index(fields=["organization", "is_trashed"]),
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_template"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ["completed"]:
            return self.due_date < timezone.now()
        return False

    @property
    def subtask_count(self):
        return self.subtasks.count()

    @property
    def completed_subtask_count(self):
        return self.subtasks.filter(status="completed").count()

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
            "todo": "#6b7280", "in_progress": "#3b82f6", "review": "#a855f7",
            "completed": "#22c55e", "on_hold": "#f97316",
            "scheduled": "#06b6d4", "overdue": "#ef4444",
        }
        return colors.get(self.status, "#6b7280")

    @property
    def assignee_list(self):
        return self.assigned_to.select_related('user').all()


class TaskStep(models.Model):
    """Steps within a task (ordered checklist items)."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    completed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        indexes = [models.Index(fields=["task", "order"])]

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["task", "created_at"])]

    def __str__(self):
        return f"Comment on {self.task.title}"


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

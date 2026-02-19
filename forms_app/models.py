"""Forms app models: Form builder with fields, responses."""
from django.db import models
from core.models import Organization, Outlet, Team, UserProfile


class Form(models.Model):
    STATUS_CHOICES = [
        ("saved", "Saved"),
        ("published", "Published"),
        ("trashed", "Trashed"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="forms")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, related_name="forms")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="forms")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="saved")
    fields_schema = models.JSONField(default=list, blank=True, help_text="Form field definitions")
    assigned_to = models.ManyToManyField(UserProfile, blank=True, related_name="assigned_forms")
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="created_forms")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "outlet"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name

    @property
    def response_count(self):
        return self.responses.count()

    @property
    def open_response_count(self):
        return self.responses.filter(status="open").count()


class FormResponse(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("submitted", "Submitted"),
        ("reviewed", "Reviewed"),
    ]

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="responses")
    submitted_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["form", "status"]),
        ]

    def __str__(self):
        return f"Response to {self.form.name}"

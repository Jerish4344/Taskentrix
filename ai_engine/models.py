"""AI Engine models: Store AI predictions, analysis results."""
from django.db import models
from core.models import Organization, UserProfile


class AIAnalysis(models.Model):
    """Store AI analysis results for caching."""
    TYPE_CHOICES = [
        ("summary", "Task Summary"),
        ("priority", "Priority Prediction"),
        ("delay", "Delay Prediction"),
        ("workload", "Workload Analysis"),
        ("similarity", "Similarity Detection"),
        ("reminder", "Smart Reminder"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="ai_analyses")
    analysis_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField(null=True, blank=True)
    input_data = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    confidence = models.FloatField(default=0.0)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "analysis_type"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]
        verbose_name_plural = "AI Analyses"

    def __str__(self):
        return f"{self.analysis_type} - {self.entity_type} #{self.entity_id}"

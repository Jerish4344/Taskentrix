"""
Celery tasks for report cache refresh.
"""
from celery import shared_task


@shared_task
def refresh_report_cache():
    """Refresh cached report data."""
    from core.models import Organization
    from reports.models import ReportCache

    # Clear expired cache entries
    from django.utils import timezone
    ReportCache.objects.filter(expires_at__lt=timezone.now()).delete()

    return "Report cache refreshed"

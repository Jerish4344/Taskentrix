"""
Celery tasks for notifications and overdue checking.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def check_overdue_tasks():
    """Check for overdue tasks and create notifications."""
    from tasks.models import Task
    from core.models import Organization
    from notifications.models import Notification

    now = timezone.now()
    orgs = Organization.objects.filter(is_active=True)

    count = 0
    for org in orgs:
        overdue = Task.objects.filter(
            organization=org, is_trashed=False,
            due_date__lt=now, status__in=["todo", "in_progress", "review"],
        ).prefetch_related("assigned_to")

        for task in overdue:
            if task.status != "overdue":
                task.status = "overdue"
                task.save(update_fields=["status"])

            for assignee in task.assigned_to.all():
                exists = Notification.objects.filter(
                    user=assignee, entity_type="task", entity_id=task.id,
                    notification_type="task_overdue",
                    created_at__gte=now - timedelta(hours=24),
                ).exists()
                if not exists:
                    Notification.objects.create(
                        organization=org, user=assignee,
                        notification_type="task_overdue",
                        title="Task Overdue",
                        message=f"'{task.title}' is past its due date.",
                        link=f"/tasks/{task.id}/",
                        entity_type="task", entity_id=task.id,
                        priority="high",
                    )
                    count += 1

    return f"Created {count} overdue notifications"


@shared_task
def send_smart_reminders():
    """Send smart AI-based reminders."""
    from core.models import Organization
    from core.ai_engine import AIEngine
    from notifications.models import Notification

    orgs = Organization.objects.filter(is_active=True)
    count = 0

    for org in orgs:
        reminders = AIEngine.generate_smart_reminders(org)
        for r in reminders:
            from tasks.models import Task
            try:
                task = Task.objects.get(id=r["task_id"])
            except Task.DoesNotExist:
                continue

            for assignee in task.assigned_to.all():
                Notification.objects.create(
                    organization=org, user=assignee,
                    notification_type="reminder",
                    title=f"Smart Reminder: {r['type'].replace('_', ' ').title()}",
                    message=r["message"],
                    link=f"/tasks/{task.id}/",
                    entity_type="task", entity_id=task.id,
                    priority=r.get("priority", "normal"),
                )
                count += 1

    return f"Sent {count} smart reminders"


@shared_task
def process_recurring_tasks():
    """Create new instances of recurring tasks that are due."""
    from tasks.models import Task
    from core.models import Organization

    now = timezone.now()
    count = 0

    recurring = Task.objects.filter(
        is_trashed=False, status="completed",
        recurrence__in=["daily", "weekly", "monthly"],
    )

    for task in recurring:
        if task.recurrence == "daily":
            next_due = task.completed_at + timedelta(days=1) if task.completed_at else now + timedelta(days=1)
        elif task.recurrence == "weekly":
            next_due = task.completed_at + timedelta(weeks=1) if task.completed_at else now + timedelta(weeks=1)
        else:
            next_due = task.completed_at + timedelta(days=30) if task.completed_at else now + timedelta(days=30)

        if next_due <= now:
            new_task = Task.objects.create(
                organization=task.organization,
                project=task.project, outlet=task.outlet, team=task.team,
                title=task.title, description=task.description,
                task_type=task.task_type, priority=task.priority,
                category=task.category, created_by=task.created_by,
                due_date=next_due, points=task.points,
                recurrence=task.recurrence,
                recurrence_details=task.recurrence_details,
            )
            new_task.assigned_to.set(task.assigned_to.all())
            count += 1

    return f"Created {count} recurring tasks"

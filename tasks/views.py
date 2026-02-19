"""
Tasks app views: list, board, calendar, create, detail, subtasks, steps.
"""
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt

from core.views import get_current_org, get_current_profile, get_current_outlet, log_activity, paginate, require_perm
from core.models import Outlet, Team, UserProfile
from projects.models import Project
from .models import Task, TaskCategory, TaskStep, TaskComment, TaskAttachment


def task_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_tasks")
    if denied:
        return denied

    tasks = Task.objects.filter(
        organization=org, is_trashed=False, parent__isnull=True
    ).select_related(
        "category", "project", "outlet", "team", "created_by", "created_by__user"
    ).prefetch_related("assigned_to", "assigned_to__user")

    outlet = get_current_outlet(request)
    if outlet:
        tasks = tasks.filter(outlet=outlet)

    # Filters
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    category = request.GET.get("category", "")
    project_id = request.GET.get("project", "")
    team_id = request.GET.get("team", "")
    assigned = request.GET.get("assigned_to", "")
    task_type = request.GET.get("task_type", "")
    search = request.GET.get("search", "")
    view_mode = request.GET.get("view", "list")
    starred = request.GET.get("starred", "")

    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if category:
        tasks = tasks.filter(category_id=category)
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if team_id:
        tasks = tasks.filter(team_id=team_id)
    if assigned:
        tasks = tasks.filter(assigned_to__id=assigned)
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    if starred:
        tasks = tasks.filter(is_starred=True)
    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))

    tasks = paginate(tasks, request)

    categories = TaskCategory.objects.filter(organization=org, is_active=True)
    projects = Project.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")
    outlets = Outlet.objects.filter(organization=org, is_active=True)

    return render(request, "tasks/list.html", {
        "tasks": tasks,
        "categories": categories, "projects": projects,
        "teams": teams, "members": members, "outlets": outlets,
        "view_mode": view_mode,
        "filters": {
            "status": status, "priority": priority, "category": category,
            "project": project_id, "team": team_id, "assigned_to": assigned,
            "task_type": task_type, "search": search, "starred": starred,
        },
        "status_choices": Task.STATUS_CHOICES,
        "priority_choices": Task.PRIORITY_CHOICES,
    })


def task_board_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_tasks")
    if denied:
        return denied

    tasks = Task.objects.filter(
        organization=org, is_trashed=False, parent__isnull=True
    ).select_related("category", "created_by", "created_by__user").prefetch_related("assigned_to", "assigned_to__user")

    outlet = get_current_outlet(request)
    if outlet:
        tasks = tasks.filter(outlet=outlet)

    columns = {
        "todo": {"label": "To Do", "color": "#6b7280", "tasks": []},
        "in_progress": {"label": "In Progress", "color": "#3b82f6", "tasks": []},
        "review": {"label": "In Review", "color": "#a855f7", "tasks": []},
        "completed": {"label": "Completed", "color": "#22c55e", "tasks": []},
        "on_hold": {"label": "On Hold", "color": "#f97316", "tasks": []},
    }
    for t in tasks:
        if t.status in columns:
            columns[t.status]["tasks"].append(t)

    return render(request, "tasks/board.html", {"columns": columns})


def task_calendar_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_tasks")
    if denied:
        return denied

    tasks = Task.objects.filter(
        organization=org, is_trashed=False, parent__isnull=True, due_date__isnull=False
    ).select_related("category").prefetch_related("assigned_to", "assigned_to__user")

    outlet = get_current_outlet(request)
    if outlet:
        tasks = tasks.filter(outlet=outlet)

    events = [{
        "id": t.id, "title": t.title, "start": t.due_date.isoformat(),
        "color": t.priority_color, "status": t.get_status_display(),
        "priority": t.get_priority_display(),
    } for t in tasks]

    return render(request, "tasks/calendar.html", {"events_json": json.dumps(events)})


def task_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_task")
    if denied:
        return denied

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            task = Task.objects.create(
                organization=org, title=title,
                description=request.POST.get("description", ""),
                sop_content=request.POST.get("sop_content", ""),
                task_type=request.POST.get("task_type", "single"),
                status=request.POST.get("status", "todo"),
                priority=request.POST.get("priority", "none"),
                category_id=request.POST.get("category") or None,
                project_id=request.POST.get("project") or None,
                outlet_id=request.POST.get("outlet") or None,
                team_id=request.POST.get("team") or None,
                created_by=profile,
                start_date=request.POST.get("start_date") or None,
                due_date=request.POST.get("due_date") or None,
                points=int(request.POST.get("points", 0) or 0),
                recurrence=request.POST.get("recurrence", "none"),
                needs_approval=request.POST.get("needs_approval") == "on",
            )
            assigned_ids = request.POST.getlist("assigned_to")
            if assigned_ids:
                task.assigned_to.set(UserProfile.objects.filter(id__in=assigned_ids, organization=org))

            # Create steps
            step_titles = request.POST.getlist("step_title")
            for i, st in enumerate(step_titles):
                if st.strip():
                    TaskStep.objects.create(task=task, title=st.strip(), order=i)

            # AI summary
            from core.ai_engine import AIEngine
            task.ai_summary = AIEngine.generate_summary({
                "title": task.title, "description": task.description, "priority": task.priority,
            })
            task.ai_priority_suggestion = AIEngine.predict_priority(task.title, task.description).get("priority", "")
            task.save(update_fields=["ai_summary", "ai_priority_suggestion"])

            log_activity(org, profile, "created", "task", task.id, task.title)

            from notifications.models import Notification
            for assignee in task.assigned_to.all():
                if assignee != profile:
                    Notification.objects.create(
                        organization=org, user=assignee,
                        notification_type="task_assigned",
                        title="New Task Assigned",
                        message=f"You've been assigned: '{task.title}'",
                        link=f"/tasks/{task.id}/",
                        entity_type="task", entity_id=task.id,
                    )

            redirect_to = request.POST.get("redirect_to", "")
            if redirect_to == "project" and task.project_id:
                return redirect("project_detail", project_id=task.project_id)
            return redirect("task_list")

    categories = TaskCategory.objects.filter(organization=org, is_active=True)
    projects = Project.objects.filter(organization=org, is_active=True)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "tasks/create.html", {
        "categories": categories, "projects": projects,
        "outlets": outlets, "teams": teams, "members": members,
        "status_choices": Task.STATUS_CHOICES,
        "priority_choices": Task.PRIORITY_CHOICES,
        "type_choices": Task.TYPE_CHOICES,
        "recurrence_choices": Task.RECURRENCE_CHOICES,
        "preselect_project": request.GET.get("project", ""),
    })


def task_detail_view(request, task_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_tasks")
    if denied:
        return denied

    task = get_object_or_404(Task, id=task_id, organization=org)
    comments = task.comments.select_related("user", "user__user").all()
    steps = task.steps.all()
    subtasks = task.subtasks.filter(is_trashed=False).select_related("category").prefetch_related("assigned_to")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update":
            old_status = task.status
            task.title = request.POST.get("title", task.title)
            task.description = request.POST.get("description", task.description)
            task.status = request.POST.get("status", task.status)
            task.priority = request.POST.get("priority", task.priority)
            task.category_id = request.POST.get("category") or task.category_id
            task.project_id = request.POST.get("project") or task.project_id
            task.outlet_id = request.POST.get("outlet") or task.outlet_id
            task.team_id = request.POST.get("team") or task.team_id
            task.due_date = request.POST.get("due_date") or task.due_date
            task.points = int(request.POST.get("points", task.points) or task.points)
            task.tags = request.POST.get("tags", task.tags)

            if task.status == "completed" and old_status != "completed":
                task.completed_at = timezone.now()
            elif task.status != "completed":
                task.completed_at = None

            task.save()
            assigned_ids = request.POST.getlist("assigned_to")
            if assigned_ids:
                task.assigned_to.set(UserProfile.objects.filter(id__in=assigned_ids, organization=org))
            log_activity(org, profile, "updated", "task", task.id, task.title)
            return redirect("task_detail", task_id=task.id)

        elif action == "comment":
            text = request.POST.get("comment", "").strip()
            if text:
                TaskComment.objects.create(task=task, user=profile, comment=text)
                log_activity(org, profile, "commented", "task", task.id, task.title)
                return redirect("task_detail", task_id=task.id)

        elif action == "add_step":
            title = request.POST.get("step_title", "").strip()
            if title:
                order = steps.count()
                TaskStep.objects.create(task=task, title=title, order=order)
                return redirect("task_detail", task_id=task.id)

        elif action == "toggle_step":
            step_id = request.POST.get("step_id")
            try:
                step = TaskStep.objects.get(id=step_id, task=task)
                step.is_completed = not step.is_completed
                step.completed_by = profile if step.is_completed else None
                step.completed_at = timezone.now() if step.is_completed else None
                step.save()
            except TaskStep.DoesNotExist:
                pass
            return redirect("task_detail", task_id=task.id)

        elif action == "star":
            task.is_starred = not task.is_starred
            task.save(update_fields=["is_starred"])
            return redirect("task_detail", task_id=task.id)

        elif action == "trash":
            task.is_trashed = True
            task.save(update_fields=["is_trashed"])
            log_activity(org, profile, "trashed", "task", task.id, task.title)
            return redirect("task_list")

        elif action == "delete":
            log_activity(org, profile, "deleted", "task", None, task.title)
            task.delete()
            return redirect("task_list")

        elif action == "ai_summary":
            from core.ai_engine import AIEngine
            task.ai_summary = AIEngine.generate_summary({
                "title": task.title, "description": task.description, "priority": task.priority,
            })
            task.save(update_fields=["ai_summary"])
            return redirect("task_detail", task_id=task.id)

        elif action == "add_subtask":
            sub_title = request.POST.get("subtask_title", "").strip()
            if sub_title:
                Task.objects.create(
                    organization=org, parent=task, title=sub_title,
                    status="todo", priority=task.priority,
                    project=task.project, outlet=task.outlet, team=task.team,
                    created_by=profile,
                )
                return redirect("task_detail", task_id=task.id)

    categories = TaskCategory.objects.filter(organization=org, is_active=True)
    projects = Project.objects.filter(organization=org, is_active=True)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "tasks/detail.html", {
        "task": task, "comments": comments, "steps": steps, "subtasks": subtasks,
        "categories": categories, "projects": projects,
        "outlets": outlets, "teams": teams, "members": members,
        "status_choices": Task.STATUS_CHOICES,
        "priority_choices": Task.PRIORITY_CHOICES,
    })


@csrf_exempt
def api_task_status_update(request, task_id):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("change_task_status"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            data = json.loads(request.body)
            task = Task.objects.get(id=task_id, organization=org)
            old_status = task.status
            task.status = data.get("status", task.status)
            if task.status == "completed" and old_status != "completed":
                task.completed_at = timezone.now()
            elif task.status != "completed":
                task.completed_at = None
            task.save()
            log_activity(org, profile, "status_changed", "task", task.id, task.title,
                        f"{old_status} → {task.status}")
            return JsonResponse({"success": True})
        except Task.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_task_star_toggle(request, task_id):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("edit_task"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            task = Task.objects.get(id=task_id, organization=org)
            task.is_starred = not task.is_starred
            task.save(update_fields=["is_starred"])
            return JsonResponse({"success": True, "is_starred": task.is_starred})
        except Task.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)

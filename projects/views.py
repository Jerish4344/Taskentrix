"""
Projects app views: list, board, create, detail, edit.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt

from core.views import get_current_org, get_current_profile, get_current_outlet, log_activity, paginate, require_perm
from core.models import Outlet, UserProfile
from .models import Project, ProjectTag


def project_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_projects")
    if denied:
        return denied

    projects = Project.objects.filter(organization=org, is_active=True).select_related(
        "outlet", "created_by", "created_by__user"
    ).prefetch_related("tags", "members")

    outlet = get_current_outlet(request)
    if outlet:
        projects = projects.filter(outlet=outlet)

    status = request.GET.get("status", "")
    search = request.GET.get("search", "")
    view_mode = request.GET.get("view", "list")

    if status:
        projects = projects.filter(status=status)
    if search:
        projects = projects.filter(Q(name__icontains=search) | Q(description__icontains=search))

    projects = paginate(projects, request)
    tags = ProjectTag.objects.filter(organization=org)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "projects/list.html", {
        "projects": projects, "tags": tags, "outlets": outlets, "members": members,
        "view_mode": view_mode,
        "filters": {"status": status, "search": search},
        "status_choices": Project.STATUS_CHOICES,
    })


def project_board_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_projects")
    if denied:
        return denied

    projects = Project.objects.filter(organization=org, is_active=True).select_related(
        "outlet", "created_by", "created_by__user"
    ).prefetch_related("tags", "members")

    outlet = get_current_outlet(request)
    if outlet:
        projects = projects.filter(outlet=outlet)

    columns = {
        "active": {"label": "Active", "color": "#3b82f6", "projects": []},
        "on_hold": {"label": "On Hold", "color": "#f97316", "projects": []},
        "completed": {"label": "Completed", "color": "#22c55e", "projects": []},
        "archived": {"label": "Archived", "color": "#6b7280", "projects": []},
    }
    for p in projects:
        if p.status in columns:
            columns[p.status]["projects"].append(p)

    return render(request, "projects/board.html", {"columns": columns})


def project_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_project")
    if denied:
        return denied

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            project = Project.objects.create(
                organization=org, name=name,
                description=request.POST.get("description", ""),
                status=request.POST.get("status", "active"),
                outlet_id=request.POST.get("outlet") or None,
                created_by=profile,
                start_date=request.POST.get("start_date") or None,
                end_date=request.POST.get("end_date") or None,
            )
            member_ids = request.POST.getlist("members")
            if member_ids:
                project.members.set(UserProfile.objects.filter(id__in=member_ids, organization=org))
            tag_ids = request.POST.getlist("tags")
            if tag_ids:
                project.tags.set(ProjectTag.objects.filter(id__in=tag_ids, organization=org))

            log_activity(org, profile, "created", "project", project.id, project.name)
            return redirect("project_list")

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")
    tags = ProjectTag.objects.filter(organization=org)

    return render(request, "projects/create.html", {
        "outlets": outlets, "members": members, "tags": tags,
        "status_choices": Project.STATUS_CHOICES,
    })


def project_detail_view(request, project_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_projects")
    if denied:
        return denied

    project = get_object_or_404(Project, id=project_id, organization=org)

    from tasks.models import Task
    tasks = Task.objects.filter(organization=org, project=project, is_trashed=False, parent__isnull=True).select_related(
        "category", "created_by", "created_by__user"
    ).prefetch_related("assigned_to", "assigned_to__user")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update":
            project.name = request.POST.get("name", project.name)
            project.description = request.POST.get("description", project.description)
            project.status = request.POST.get("status", project.status)
            project.outlet_id = request.POST.get("outlet") or project.outlet_id
            project.start_date = request.POST.get("start_date") or project.start_date
            project.end_date = request.POST.get("end_date") or project.end_date
            project.save()
            member_ids = request.POST.getlist("members")
            if member_ids:
                project.members.set(UserProfile.objects.filter(id__in=member_ids, organization=org))
            log_activity(org, profile, "updated", "project", project.id, project.name)
            return redirect("project_detail", project_id=project.id)

        elif action == "delete":
            log_activity(org, profile, "deleted", "project", None, project.name)
            project.is_active = False
            project.save()
            return redirect("project_list")

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")
    tags = ProjectTag.objects.filter(organization=org)

    # Task board columns for the project
    task_columns = {
        "todo": {"label": "To Do", "color": "#6b7280", "tasks": []},
        "in_progress": {"label": "In Progress", "color": "#3b82f6", "tasks": []},
        "review": {"label": "In Review", "color": "#a855f7", "tasks": []},
        "completed": {"label": "Completed", "color": "#22c55e", "tasks": []},
    }
    for t in tasks:
        if t.status in task_columns:
            task_columns[t.status]["tasks"].append(t)

    return render(request, "projects/detail.html", {
        "project": project, "tasks": tasks, "task_columns": task_columns,
        "outlets": outlets, "members": members, "tags": tags,
        "status_choices": Project.STATUS_CHOICES,
    })


@csrf_exempt
def api_project_status_update(request, project_id):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("edit_project"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            data = json.loads(request.body)
            project = Project.objects.get(id=project_id, organization=org)
            project.status = data.get("status", project.status)
            project.save()
            return JsonResponse({"success": True})
        except Project.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)

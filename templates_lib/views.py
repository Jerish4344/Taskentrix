"""
Templates Library views: browse, create, use templates.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from core.views import get_current_org, get_current_profile, log_activity, paginate, require_perm
from core.models import Outlet, Team, UserProfile
from .models import TemplateCategory, TemplateIndustry, TaskTemplate, TaskTemplateSubtask, ProjectTemplate


def template_library_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_templates")
    if denied:
        return denied

    tab = request.GET.get("tab", "task")
    search = request.GET.get("search", "")
    category_id = request.GET.get("category", "")
    industry_id = request.GET.get("industry", "")

    if tab == "project":
        templates = ProjectTemplate.objects.filter(
            Q(organization=org) | Q(organization__isnull=True), is_active=True
        )
        if search:
            templates = templates.filter(Q(name__icontains=search) | Q(description__icontains=search))
        templates = paginate(templates, request)
    else:
        templates = TaskTemplate.objects.filter(
            Q(organization=org) | Q(organization__isnull=True), is_active=True
        ).select_related("category").prefetch_related("industries")

        if search:
            templates = templates.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if category_id:
            templates = templates.filter(category_id=category_id)
        if industry_id:
            templates = templates.filter(industries__id=industry_id)
        templates = paginate(templates, request)

    categories = TemplateCategory.objects.all()
    industries = TemplateIndustry.objects.all()

    return render(request, "templates_lib/library.html", {
        "templates": templates, "categories": categories, "industries": industries,
        "tab": tab,
        "filters": {"search": search, "category": category_id, "industry": industry_id},
    })


def template_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_template")
    if denied:
        return denied

    tab = request.GET.get("tab", "task")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            return redirect("template_library")

        if tab == "project":
            ProjectTemplate.objects.create(
                organization=org, name=name,
                description=request.POST.get("description", ""),
                default_status=request.POST.get("default_status", "active"),
                created_by=profile,
            )
        else:
            tpl = TaskTemplate.objects.create(
                organization=org, name=name,
                description=request.POST.get("description", ""),
                default_priority=request.POST.get("default_priority", "none"),
                default_points=int(request.POST.get("default_points", 0) or 0),
                recurrence=request.POST.get("recurrence", "none"),
                category_id=request.POST.get("category") or None,
                created_by=profile,
            )
            industry_ids = request.POST.getlist("industries")
            if industry_ids:
                tpl.industries.set(TemplateIndustry.objects.filter(id__in=industry_ids))

            subtask_titles = request.POST.getlist("subtask_title")
            for i, st in enumerate(subtask_titles):
                if st.strip():
                    TaskTemplateSubtask.objects.create(template=tpl, title=st.strip(), order=i)

        log_activity(org, profile, "created", "template", None, name)
        return redirect("template_library")

    categories = TemplateCategory.objects.all()
    industries = TemplateIndustry.objects.all()
    return render(request, "templates_lib/create.html", {
        "categories": categories, "industries": industries, "tab": tab,
    })


def template_use_view(request, template_id):
    """Use a task template to create a new task."""
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_template")
    if denied:
        return denied

    template = get_object_or_404(TaskTemplate, id=template_id)
    subtasks = template.subtasks.all()

    from tasks.models import Task, TaskStep
    from projects.models import Project

    if request.method == "POST":
        task = Task.objects.create(
            organization=org,
            title=request.POST.get("title", template.name),
            description=template.description,
            priority=template.default_priority,
            points=template.default_points,
            recurrence=template.recurrence,
            created_by=profile,
            outlet_id=request.POST.get("outlet") or None,
            project_id=request.POST.get("project") or None,
            team_id=request.POST.get("team") or None,
            due_date=request.POST.get("due_date") or None,
        )
        assigned_ids = request.POST.getlist("assigned_to")
        if assigned_ids:
            task.assigned_to.set(UserProfile.objects.filter(id__in=assigned_ids, organization=org))

        for sub in subtasks:
            TaskStep.objects.create(task=task, title=sub.title, order=sub.order)

        log_activity(org, profile, "used_template", "task", task.id, template.name)
        return redirect("task_detail", task_id=task.id)

    from projects.models import Project
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    projects = Project.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "templates_lib/use.html", {
        "template": template, "subtasks": subtasks,
        "outlets": outlets, "projects": projects, "teams": teams, "members": members,
    })


def template_detail_view(request, template_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_templates")
    if denied:
        return denied

    tab = request.GET.get("tab", "task")

    if tab == "project":
        template = get_object_or_404(ProjectTemplate, id=template_id)
        return render(request, "templates_lib/detail_project.html", {"template": template})
    else:
        template = get_object_or_404(TaskTemplate, id=template_id)
        subtasks = template.subtasks.all()
        return render(request, "templates_lib/detail.html", {"template": template, "subtasks": subtasks})

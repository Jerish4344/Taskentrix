"""
Core views: Authentication, Dashboard, Users, Roles, Outlets, Teams, Activity Log.
"""
import json
import random
import requests
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core.cache import cache
from django.conf import settings

from .models import (
    Organization, Outlet, Team, Permission, Role,
    UserProfile, ActivityLog,
)


# ============================================================
# HELPERS (used across all apps)
# ============================================================

def get_current_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return UserProfile.objects.select_related(
            "user", "organization", "role", "outlet", "team"
        ).get(id=user_id)
    except UserProfile.DoesNotExist:
        return None


def get_current_org(request):
    org_id = request.session.get("current_org_id")
    if org_id:
        try:
            return Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            pass
    profile = get_current_profile(request)
    if profile:
        request.session["current_org_id"] = profile.organization.id
        return profile.organization
    return None


def get_current_outlet(request):
    outlet_id = request.session.get("current_outlet_id")
    if outlet_id:
        try:
            return Outlet.objects.get(id=outlet_id)
        except Outlet.DoesNotExist:
            pass
    return None


def log_activity(org, user_profile, action, entity_type, entity_id=None, entity_name="", details=""):
    ActivityLog.objects.create(
        organization=org, user=user_profile, action=action,
        entity_type=entity_type, entity_id=entity_id,
        entity_name=entity_name, details=details,
    )


def paginate(queryset, request, per_page=None):
    per_page = per_page or int(request.GET.get("per_page", getattr(settings, "DEFAULT_PAGE_SIZE", 10)))
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page", 1))


def require_perm(profile, codename):
    """Return a redirect response if the user lacks the given permission, else None."""
    if not profile or not profile.has_perm(codename):
        from django.http import HttpResponseForbidden
        return render_no_perm()
    return None


def render_no_perm():
    """Return a styled 403 Forbidden response."""
    from django.http import HttpResponseForbidden
    html = """
    <!DOCTYPE html><html><head><title>Access Denied</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body{font-family:'Inter',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f9fafb;}
    .card{text-align:center;padding:3rem;background:#fff;border-radius:1rem;box-shadow:0 1px 3px rgba(0,0,0,.1);max-width:420px;}
    .icon{font-size:3rem;margin-bottom:1rem;}
    h1{font-size:1.5rem;color:#1f2937;margin:.5rem 0;}
    p{color:#6b7280;font-size:.95rem;line-height:1.6;}
    a{display:inline-block;margin-top:1.5rem;padding:.6rem 1.5rem;background:#6366f1;color:#fff;border-radius:.5rem;text-decoration:none;font-weight:600;font-size:.9rem;}
    a:hover{background:#4f46e5;}</style></head>
    <body><div class="card"><div class="icon">🔒</div><h1>Access Denied</h1>
    <p>You don't have permission to access this page. Contact your administrator to request access.</p>
    <a href="/dashboard/">← Back to Dashboard</a></div></body></html>
    """
    return HttpResponseForbidden(html)


# ============================================================
# AUTHENTICATION
# ============================================================

def login_view(request):
    if request.session.get("user_id"):
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            error = "Please enter both email and password."
        else:
            profile = None
            try:
                response = requests.post(
                    settings.STYLEHR_LOGIN_API,
                    json={"email": email, "password": password},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and data.get("id"):
                        profile = _handle_api_login(data, email)
            except (requests.RequestException, ValueError, KeyError):
                pass

            if not profile:
                profile = _handle_local_login(email, password)

            if profile:
                request.session["user_id"] = profile.id
                request.session["current_org_id"] = profile.organization.id
                if profile.outlet:
                    request.session["current_outlet_id"] = profile.outlet.id
                profile.last_login_at = timezone.now()
                profile.save(update_fields=["last_login_at"])
                log_activity(profile.organization, profile, "login", "user", profile.id, profile.full_name)
                return redirect("dashboard")
            else:
                error = "Invalid email/employee ID or password."

    return render(request, "login.html", {"error": error})


def _handle_api_login(data, email):
    emp_name = data.get("name", data.get("employee_name", email.split("@")[0]))
    emp_id = str(data.get("id", data.get("employee_id", "")))

    try:
        profile = UserProfile.objects.get(employee_id=emp_id)
        profile.stylehr_data = data
        profile.save(update_fields=["stylehr_data"])
        return profile
    except UserProfile.DoesNotExist:
        pass

    org = Organization.objects.filter(is_active=True).first()
    if not org:
        return None

    username = f"api_{emp_id}"
    parts = emp_name.split()
    first_name = parts[0] if parts else emp_name
    last_name = parts[-1] if len(parts) > 1 else ""

    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"first_name": first_name, "last_name": last_name, "email": email}
    )
    role = Role.objects.filter(organization=org, name="Employee").first()
    return UserProfile.objects.create(
        user=user, organization=org, role=role,
        employee_id=emp_id, stylehr_data=data,
    )


def _handle_local_login(email, password):
    user = None
    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            try:
                profile = UserProfile.objects.get(employee_id=email)
                user = profile.user
            except UserProfile.DoesNotExist:
                return None

    if user and user.check_password(password):
        try:
            return user.profile
        except UserProfile.DoesNotExist:
            return None
    return None


def logout_view(request):
    profile = get_current_profile(request)
    if profile:
        log_activity(profile.organization, profile, "logout", "user", profile.id, profile.full_name)
    request.session.flush()
    return redirect("login")


# ============================================================
# ORG / OUTLET SWITCH
# ============================================================

def switch_organization(request, org_id):
    try:
        org = Organization.objects.get(id=org_id, is_active=True)
        request.session["current_org_id"] = org.id
        request.session.pop("current_outlet_id", None)
    except Organization.DoesNotExist:
        pass
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


def switch_outlet(request, outlet_id):
    try:
        outlet = Outlet.objects.get(id=outlet_id, is_active=True)
        request.session["current_outlet_id"] = outlet.id
    except Outlet.DoesNotExist:
        pass
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


def clear_outlet(request):
    request.session.pop("current_outlet_id", None)
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")

    from tasks.models import Task
    from issues.models import Issue
    from projects.models import Project
    from forms_app.models import Form

    outlet = get_current_outlet(request)

    # Outlet-wise summary for home page (like Petpooja)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    outlet_summary = []
    for o in outlets:
        t = Task.objects.filter(organization=org, outlet=o, is_trashed=False)
        i = Issue.objects.filter(organization=org, outlet=o, is_trashed=False)
        f = Form.objects.filter(organization=org, outlet=o)
        outlet_summary.append({
            "outlet": o,
            "tasks_total": t.count(),
            "tasks_ongoing": t.filter(status="in_progress").count(),
            "tasks_completed": t.filter(status="completed").count(),
            "tasks_overdue": t.filter(due_date__lt=timezone.now(), status__in=["todo", "in_progress"]).count(),
            "tasks_scheduled": t.filter(status="scheduled").count(),
            "issues_total": i.count(),
            "issues_open": i.filter(status="open").count(),
            "issues_ignored": i.filter(status="ignored").count(),
            "issues_resolved": i.filter(status="resolved").count(),
            "forms_total": f.count(),
            "forms_ongoing": f.filter(status="published").count(),
            "forms_open_responses": sum(fm.open_response_count for fm in f),
            "forms_submitted": sum(fm.response_count for fm in f),
        })

    # Global stats
    task_qs = Task.objects.filter(organization=org, is_trashed=False)
    if outlet:
        task_qs = task_qs.filter(outlet=outlet)

    total_tasks = task_qs.count()
    ongoing = task_qs.filter(status="in_progress").count()
    completed = task_qs.filter(status="completed").count()
    overdue = task_qs.filter(due_date__lt=timezone.now()).exclude(status="completed").count()
    scheduled = task_qs.filter(status="scheduled").count()

    projects = Project.objects.filter(organization=org, is_active=True)
    if outlet:
        projects = projects.filter(outlet=outlet)

    issue_qs = Issue.objects.filter(organization=org, is_trashed=False)
    if outlet:
        issue_qs = issue_qs.filter(outlet=outlet)

    form_qs = Form.objects.filter(organization=org)
    if outlet:
        form_qs = form_qs.filter(outlet=outlet)

    # AI Reviews placeholder
    from ai_engine.models import AIAnalysis
    ai_reviews = AIAnalysis.objects.filter(organization=org).count()

    recent_activities = ActivityLog.objects.filter(
        organization=org
    ).select_related("user", "user__user")[:10]

    context = {
        "org": org,
        "outlet": outlet,
        "outlet_summary": outlet_summary,
        "projects_count": projects.count(),
        "total_tasks": total_tasks,
        "ongoing": ongoing,
        "completed": completed,
        "overdue": overdue,
        "scheduled": scheduled,
        "ai_reviews": ai_reviews,
        "issues_count": issue_qs.count(),
        "issues_open": issue_qs.filter(status="open").count(),
        "issues_ignored": issue_qs.filter(status="ignored").count(),
        "issues_resolved": issue_qs.filter(status="resolved").count(),
        "forms_count": form_qs.count(),
        "recent_activities": recent_activities,
    }
    return render(request, "dashboard.html", context)


# ============================================================
# OUTLETS
# ============================================================

def outlet_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "manage_outlets")
    if denied: return denied
    outlets = Outlet.objects.filter(organization=org)
    outlets = paginate(outlets, request, 25)
    return render(request, "outlets/list.html", {"outlets": outlets})


def outlet_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "manage_outlets")
    if denied: return denied

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Outlet.objects.create(
                organization=org, name=name,
                code=request.POST.get("code", ""),
                address=request.POST.get("address", ""),
                phone=request.POST.get("phone", ""),
                email=request.POST.get("email", ""),
            )
            log_activity(org, profile, "created", "outlet", None, name)
            return redirect("outlet_list")

    return render(request, "outlets/create.html")


def outlet_edit_view(request, outlet_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "manage_outlets")
    if denied: return denied

    outlet = get_object_or_404(Outlet, id=outlet_id, organization=org)

    if request.method == "POST":
        action = request.POST.get("action", "update")
        if action == "delete":
            outlet.delete()
            log_activity(org, profile, "deleted", "outlet", None, outlet.name)
            return redirect("outlet_list")

        outlet.name = request.POST.get("name", outlet.name)
        outlet.code = request.POST.get("code", outlet.code)
        outlet.address = request.POST.get("address", outlet.address)
        outlet.phone = request.POST.get("phone", outlet.phone)
        outlet.email = request.POST.get("email", outlet.email)
        outlet.is_active = request.POST.get("is_active") == "on"
        outlet.save()
        log_activity(org, profile, "updated", "outlet", outlet.id, outlet.name)
        return redirect("outlet_list")

    return render(request, "outlets/edit.html", {"outlet": outlet})


# ============================================================
# TEAMS
# ============================================================

def team_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "manage_outlets")
    if denied: return denied
    teams = Team.objects.filter(organization=org).annotate(member_count=Count("members"))
    return render(request, "teams/list.html", {"teams": teams})


def team_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "manage_outlets")
    if denied: return denied

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Team.objects.create(
                organization=org, name=name,
                description=request.POST.get("description", ""),
                color=request.POST.get("color", "#6366f1"),
            )
            log_activity(org, profile, "created", "team", None, name)
            return redirect("team_list")

    return render(request, "teams/create.html")


def team_edit_view(request, team_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "manage_outlets")
    if denied: return denied

    team = get_object_or_404(Team, id=team_id, organization=org)

    if request.method == "POST":
        action = request.POST.get("action", "update")
        if action == "delete":
            team.delete()
            log_activity(org, profile, "deleted", "team", None, team.name)
            return redirect("team_list")

        team.name = request.POST.get("name", team.name)
        team.description = request.POST.get("description", team.description)
        team.color = request.POST.get("color", team.color)
        team.is_active = request.POST.get("is_active") == "on"
        team.save()
        log_activity(org, profile, "updated", "team", team.id, team.name)
        return redirect("team_list")

    return render(request, "teams/edit.html", {"team": team})


# ============================================================
# USERS
# ============================================================

def user_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_users")
    if denied: return denied

    users = UserProfile.objects.filter(organization=org).select_related(
        "user", "role", "outlet", "team"
    )

    search = request.GET.get("search", "")
    if search:
        users = users.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(employee_id__icontains=search)
        )

    users = paginate(users, request)
    roles = Role.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    return render(request, "users/list.html", {"users": users, "roles": roles, "teams": teams})


def user_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_user")
    if denied: return denied

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        if username and email:
            user = User.objects.create_user(
                username=username, email=email,
                first_name=request.POST.get("first_name", ""),
                last_name=request.POST.get("last_name", ""),
                password=request.POST.get("password", "password123"),
            )
            colors = ["#6366f1", "#ec4899", "#8b5cf6", "#06b6d4", "#f59e0b", "#10b981"]
            UserProfile.objects.create(
                user=user, organization=org,
                role_id=request.POST.get("role") or None,
                outlet_id=request.POST.get("outlet") or None,
                team_id=request.POST.get("team") or None,
                employee_id=request.POST.get("employee_id", ""),
                phone=request.POST.get("phone", ""),
                department=request.POST.get("department", ""),
                designation=request.POST.get("designation", ""),
                avatar_color=random.choice(colors),
            )
            log_activity(org, profile, "created", "user", None, f"{user.first_name} {user.last_name}")
            return redirect("user_list")

    roles = Role.objects.filter(organization=org, is_active=True)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    return render(request, "users/create.html", {"roles": roles, "outlets": outlets, "teams": teams})


def user_edit_view(request, user_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "edit_user")
    if denied: return denied

    target = get_object_or_404(UserProfile, id=user_id, organization=org)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            target.user.delete()
            log_activity(org, profile, "deleted", "user", None, target.full_name)
            return redirect("user_list")

        target.user.first_name = request.POST.get("first_name", target.user.first_name)
        target.user.last_name = request.POST.get("last_name", target.user.last_name)
        target.user.email = request.POST.get("email", target.user.email)
        target.user.save()

        target.role_id = request.POST.get("role") or target.role_id
        target.outlet_id = request.POST.get("outlet") or target.outlet_id
        target.team_id = request.POST.get("team") or target.team_id
        target.department = request.POST.get("department", target.department)
        target.designation = request.POST.get("designation", target.designation)
        target.employee_id = request.POST.get("employee_id", target.employee_id)
        target.phone = request.POST.get("phone", target.phone)
        target.is_active = request.POST.get("is_active") == "on"
        target.save()
        log_activity(org, profile, "updated", "user", target.id, target.full_name)
        return redirect("user_list")

    roles = Role.objects.filter(organization=org, is_active=True)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    return render(request, "users/edit.html", {
        "target_profile": target, "roles": roles, "outlets": outlets, "teams": teams,
    })


# ============================================================
# ROLES & PERMISSIONS
# ============================================================

def role_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_roles")
    if denied: return denied
    roles = Role.objects.filter(organization=org).annotate(
        user_count=Count("users"), permission_count=Count("permissions"),
    )
    return render(request, "roles/list.html", {"roles": roles})


def role_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_role")
    if denied: return denied

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            role = Role.objects.create(organization=org, name=name, description=request.POST.get("description", ""))
            pids = request.POST.getlist("permissions")
            if pids:
                role.permissions.set(Permission.objects.filter(id__in=pids))
            log_activity(org, profile, "created", "role", role.id, role.name)
            return redirect("role_list")

    permissions = Permission.objects.all().order_by("module", "name")
    modules = {}
    for p in permissions:
        modules.setdefault(p.module, {"label": p.get_module_display(), "permissions": []})
        modules[p.module]["permissions"].append(p)
    return render(request, "roles/create.html", {"modules": modules})


def role_edit_view(request, role_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_role")
    if denied: return denied

    role = get_object_or_404(Role, id=role_id, organization=org)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            role.delete()
            log_activity(org, profile, "deleted", "role", None, role.name)
            return redirect("role_list")

        role.name = request.POST.get("name", role.name)
        role.description = request.POST.get("description", role.description)
        role.save()
        role.permissions.set(Permission.objects.filter(id__in=request.POST.getlist("permissions")))
        log_activity(org, profile, "updated", "role", role.id, role.name)
        return redirect("role_list")

    permissions = Permission.objects.all().order_by("module", "name")
    modules = {}
    for p in permissions:
        modules.setdefault(p.module, {"label": p.get_module_display(), "permissions": []})
        modules[p.module]["permissions"].append(p)
    role_perm_ids = set(role.permissions.values_list("id", flat=True))
    return render(request, "roles/edit.html", {"role": role, "modules": modules, "role_perm_ids": role_perm_ids})


# ============================================================
# ACTIVITY LOG
# ============================================================

def activity_log_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_users")
    if denied:
        return denied

    activities = ActivityLog.objects.filter(organization=org).select_related("user", "user__user")
    search = request.GET.get("search", "").strip()
    action = request.GET.get("action", "").strip()
    if search:
        activities = activities.filter(Q(entity_name__icontains=search) | Q(details__icontains=search))
    if action:
        activities = activities.filter(action=action)

    activities = paginate(activities, request, 50)
    return render(request, "activity_log.html", {"activities": activities})


# ============================================================
# API ENDPOINTS
# ============================================================

def api_dashboard_data(request):
    org = get_current_org(request)
    if not org:
        return JsonResponse({"error": "No organization"}, status=400)

    from tasks.models import Task
    tasks = Task.objects.filter(organization=org, is_trashed=False)

    data = {
        "status": {
            "labels": ["To Do", "In Progress", "In Review", "Completed", "On Hold"],
            "data": [tasks.filter(status=s).count() for s in ["todo", "in_progress", "review", "completed", "on_hold"]],
            "colors": ["#6b7280", "#3b82f6", "#a855f7", "#22c55e", "#f97316"],
        },
        "priority": {
            "labels": ["Critical", "High", "Medium", "Low"],
            "data": [tasks.filter(priority=p).count() for p in ["critical", "high", "medium", "low"]],
            "colors": ["#ef4444", "#f97316", "#eab308", "#22c55e"],
        },
    }
    return JsonResponse(data)


def api_notifications(request):
    profile = get_current_profile(request)
    if not profile:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    from notifications.models import Notification
    if request.method == "POST":
        Notification.objects.filter(user=profile, is_read=False).update(is_read=True)
        return JsonResponse({"success": True})

    notifs = Notification.objects.filter(user=profile)[:20]
    data = [{
        "id": n.id, "title": n.title, "message": n.message,
        "is_read": n.is_read, "link": n.link,
        "created_at": n.created_at.strftime("%b %d, %Y %I:%M %p"),
    } for n in notifs]
    return JsonResponse({"notifications": data})
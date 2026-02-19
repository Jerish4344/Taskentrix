"""
Reports app views: dashboard, outlet-wise, employee-wise, backlog, points.
"""
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg

from core.views import get_current_org, get_current_profile, get_current_outlet, require_perm
from core.models import Outlet, Team, UserProfile
from tasks.models import Task
from issues.models import Issue


def reports_dashboard_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    return render(request, "reports/dashboard.html")


def report_outlet_tasks_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    data = []
    for o in outlets:
        tasks = Task.objects.filter(organization=org, outlet=o, is_trashed=False)
        data.append({
            "outlet": o,
            "total": tasks.count(),
            "completed": tasks.filter(status="completed").count(),
            "ongoing": tasks.filter(status__in=["todo", "in_progress", "review"]).count(),
            "overdue": tasks.filter(due_date__lt=timezone.now()).exclude(status="completed").count(),
            "on_hold": tasks.filter(status="on_hold").count(),
        })

    return render(request, "reports/outlet_tasks.html", {"data": data})


def report_outlet_issues_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    data = []
    for o in outlets:
        issues = Issue.objects.filter(organization=org, outlet=o, is_trashed=False)
        data.append({
            "outlet": o,
            "total": issues.count(),
            "open": issues.filter(status="open").count(),
            "resolved": issues.filter(status="resolved").count(),
            "ignored": issues.filter(status="ignored").count(),
            "closed": issues.filter(status="closed").count(),
        })

    return render(request, "reports/outlet_issues.html", {"data": data})


def report_employee_tasks_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user", "outlet", "team")
    data = []
    for m in members:
        tasks = Task.objects.filter(organization=org, assigned_to=m, is_trashed=False)
        data.append({
            "member": m,
            "total": tasks.count(),
            "completed": tasks.filter(status="completed").count(),
            "ongoing": tasks.filter(status__in=["todo", "in_progress", "review"]).count(),
            "overdue": tasks.filter(due_date__lt=timezone.now()).exclude(status="completed").count(),
            "points": tasks.filter(status="completed").aggregate(total=Sum("points"))["total"] or 0,
        })

    return render(request, "reports/employee_tasks.html", {"data": data})


def report_employee_issues_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user", "outlet", "team")
    data = []
    for m in members:
        issues = Issue.objects.filter(organization=org, assigned_to=m, is_trashed=False)
        data.append({
            "member": m,
            "total": issues.count(),
            "open": issues.filter(status="open").count(),
            "resolved": issues.filter(status="resolved").count(),
            "ignored": issues.filter(status="ignored").count(),
        })

    return render(request, "reports/employee_issues.html", {"data": data})


def report_backlog_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    overdue_tasks = Task.objects.filter(
        organization=org, is_trashed=False,
        due_date__lt=timezone.now()
    ).exclude(status="completed").select_related(
        "outlet", "team", "category"
    ).prefetch_related("assigned_to", "assigned_to__user")

    outlet = get_current_outlet(request)
    if outlet:
        overdue_tasks = overdue_tasks.filter(outlet=outlet)

    return render(request, "reports/backlog.html", {"overdue_tasks": overdue_tasks})


def report_points_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_reports")
    if denied:
        return denied

    members = UserProfile.objects.filter(
        organization=org, is_active=True
    ).select_related("user", "outlet", "team")

    data = []
    for m in members:
        completed = Task.objects.filter(
            organization=org, assigned_to=m, is_trashed=False, status="completed"
        )
        data.append({
            "member": m,
            "total_points": completed.aggregate(total=Sum("points"))["total"] or 0,
            "tasks_completed": completed.count(),
        })

    data.sort(key=lambda x: x["total_points"], reverse=True)
    return render(request, "reports/points.html", {"data": data})


def api_report_chart_data(request, report_type):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    if not profile.has_perm("view_reports"):
        return JsonResponse({"error": "Permission denied"}, status=403)

    if report_type == "outlet_tasks":
        outlets = Outlet.objects.filter(organization=org, is_active=True)
        labels = [o.name for o in outlets]
        completed = [Task.objects.filter(organization=org, outlet=o, status="completed", is_trashed=False).count() for o in outlets]
        ongoing = [Task.objects.filter(organization=org, outlet=o, status__in=["todo", "in_progress"], is_trashed=False).count() for o in outlets]
        return JsonResponse({
            "labels": labels,
            "datasets": [
                {"label": "Completed", "data": completed, "backgroundColor": "#22c55e"},
                {"label": "Ongoing", "data": ongoing, "backgroundColor": "#3b82f6"},
            ]
        })

    return JsonResponse({"error": "Unknown report type"}, status=400)

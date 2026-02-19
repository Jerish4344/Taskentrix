"""
Issues app views: list, board, create, detail.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from core.views import get_current_org, get_current_profile, get_current_outlet, log_activity, paginate, require_perm
from core.models import Outlet, Team, UserProfile
from .models import Issue, IssueComment


def issue_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_issues")
    if denied:
        return denied

    issues = Issue.objects.filter(organization=org, is_trashed=False).select_related(
        "outlet", "team", "created_by", "created_by__user"
    ).prefetch_related("assigned_to", "assigned_to__user")

    outlet = get_current_outlet(request)
    if outlet:
        issues = issues.filter(outlet=outlet)

    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    search = request.GET.get("search", "")
    view_mode = request.GET.get("view", "list")

    if status:
        issues = issues.filter(status=status)
    if priority:
        issues = issues.filter(priority=priority)
    if search:
        issues = issues.filter(Q(title__icontains=search) | Q(description__icontains=search))

    issues = paginate(issues, request)
    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "issues/list.html", {
        "issues": issues, "outlets": outlets, "teams": teams, "members": members,
        "view_mode": view_mode,
        "filters": {"status": status, "priority": priority, "search": search},
        "status_choices": Issue.STATUS_CHOICES,
        "priority_choices": Issue.PRIORITY_CHOICES,
    })


def issue_board_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_issues")
    if denied:
        return denied

    issues = Issue.objects.filter(organization=org, is_trashed=False).select_related(
        "outlet", "team", "created_by", "created_by__user"
    ).prefetch_related("assigned_to", "assigned_to__user")

    outlet = get_current_outlet(request)
    if outlet:
        issues = issues.filter(outlet=outlet)

    columns = {
        "open": {"label": "Open", "color": "#ef4444", "issues": []},
        "resolved": {"label": "Resolved", "color": "#22c55e", "issues": []},
        "ignored": {"label": "Ignored", "color": "#6b7280", "issues": []},
        "closed": {"label": "Closed", "color": "#3b82f6", "issues": []},
    }
    for i in issues:
        if i.status in columns:
            columns[i.status]["issues"].append(i)

    return render(request, "issues/board.html", {"columns": columns})


def issue_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_issue")
    if denied:
        return denied

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            issue = Issue.objects.create(
                organization=org, title=title,
                description=request.POST.get("description", ""),
                priority=request.POST.get("priority", "medium"),
                outlet_id=request.POST.get("outlet") or None,
                team_id=request.POST.get("team") or None,
                created_by=profile,
                start_date=request.POST.get("start_date") or None,
                due_date=request.POST.get("due_date") or None,
                tags=request.POST.get("tags", ""),
            )
            assigned_ids = request.POST.getlist("assigned_to")
            if assigned_ids:
                issue.assigned_to.set(UserProfile.objects.filter(id__in=assigned_ids, organization=org))

            log_activity(org, profile, "created", "issue", issue.id, issue.title)

            from notifications.models import Notification
            for assignee in issue.assigned_to.all():
                if assignee != profile:
                    Notification.objects.create(
                        organization=org, user=assignee,
                        notification_type="issue_created",
                        title="New Issue Assigned",
                        message=f"Issue: '{issue.title}'",
                        link=f"/issues/{issue.id}/",
                        entity_type="issue", entity_id=issue.id,
                    )

            return redirect("issue_list")

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "issues/create.html", {
        "outlets": outlets, "teams": teams, "members": members,
        "priority_choices": Issue.PRIORITY_CHOICES,
    })


def issue_detail_view(request, issue_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_issues")
    if denied:
        return denied

    issue = get_object_or_404(Issue, id=issue_id, organization=org)
    comments = issue.comments.select_related("user", "user__user").all()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update":
            issue.title = request.POST.get("title", issue.title)
            issue.description = request.POST.get("description", issue.description)
            old_status = issue.status
            issue.status = request.POST.get("status", issue.status)
            issue.priority = request.POST.get("priority", issue.priority)
            issue.outlet_id = request.POST.get("outlet") or issue.outlet_id
            issue.team_id = request.POST.get("team") or issue.team_id
            issue.due_date = request.POST.get("due_date") or issue.due_date

            if issue.status == "resolved" and old_status != "resolved":
                issue.resolved_at = timezone.now()

            issue.save()
            assigned_ids = request.POST.getlist("assigned_to")
            if assigned_ids:
                issue.assigned_to.set(UserProfile.objects.filter(id__in=assigned_ids, organization=org))
            log_activity(org, profile, "updated", "issue", issue.id, issue.title)
            return redirect("issue_detail", issue_id=issue.id)

        elif action == "comment":
            text = request.POST.get("comment", "").strip()
            if text:
                IssueComment.objects.create(issue=issue, user=profile, comment=text)
                log_activity(org, profile, "commented", "issue", issue.id, issue.title)
                return redirect("issue_detail", issue_id=issue.id)

        elif action == "trash":
            issue.is_trashed = True
            issue.save(update_fields=["is_trashed"])
            log_activity(org, profile, "trashed", "issue", issue.id, issue.title)
            return redirect("issue_list")

        elif action == "delete":
            log_activity(org, profile, "deleted", "issue", None, issue.title)
            issue.delete()
            return redirect("issue_list")

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "issues/detail.html", {
        "issue": issue, "comments": comments,
        "outlets": outlets, "teams": teams, "members": members,
        "status_choices": Issue.STATUS_CHOICES,
        "priority_choices": Issue.PRIORITY_CHOICES,
    })


@csrf_exempt
def api_issue_status_update(request, issue_id):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("edit_issue"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            data = json.loads(request.body)
            issue = Issue.objects.get(id=issue_id, organization=org)
            issue.status = data.get("status", issue.status)
            if issue.status == "resolved":
                issue.resolved_at = timezone.now()
            issue.save()
            return JsonResponse({"success": True})
        except Issue.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"error": "Method not allowed"}, status=405)

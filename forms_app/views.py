"""
Forms app views: list, create, detail, respond, review.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from core.views import get_current_org, get_current_profile, get_current_outlet, log_activity, paginate, require_perm
from core.models import Outlet, Team, UserProfile
from .models import Form, FormResponse


def form_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_forms")
    if denied:
        return denied

    forms = Form.objects.filter(organization=org).exclude(status="trashed").select_related(
        "outlet", "team", "created_by", "created_by__user"
    )

    outlet = get_current_outlet(request)
    if outlet:
        forms = forms.filter(outlet=outlet)

    status = request.GET.get("status", "")
    search = request.GET.get("search", "")

    if status:
        forms = forms.filter(status=status)
    if search:
        forms = forms.filter(Q(title__icontains=search) | Q(description__icontains=search))

    forms = paginate(forms, request)
    return render(request, "forms/list.html", {
        "forms": forms,
        "filters": {"status": status, "search": search},
    })


def form_create_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "create_form")
    if denied:
        return denied

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            # Build fields schema from form builder
            field_labels = request.POST.getlist("field_label")
            field_types = request.POST.getlist("field_type")
            field_required = request.POST.getlist("field_required")

            fields_schema = []
            for i, label in enumerate(field_labels):
                if label.strip():
                    fields_schema.append({
                        "label": label.strip(),
                        "type": field_types[i] if i < len(field_types) else "text",
                        "required": str(i) in field_required,
                        "order": i,
                    })

            form = Form.objects.create(
                organization=org, title=title,
                description=request.POST.get("description", ""),
                status=request.POST.get("status", "saved"),
                outlet_id=request.POST.get("outlet") or None,
                team_id=request.POST.get("team") or None,
                created_by=profile,
                fields_schema=fields_schema,
                due_date=request.POST.get("due_date") or None,
            )
            assigned_ids = request.POST.getlist("assigned_to")
            if assigned_ids:
                form.assigned_to.set(UserProfile.objects.filter(id__in=assigned_ids, organization=org))

            log_activity(org, profile, "created", "form", form.id, form.title)
            return redirect("form_list")

    outlets = Outlet.objects.filter(organization=org, is_active=True)
    teams = Team.objects.filter(organization=org, is_active=True)
    members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")

    return render(request, "forms/create.html", {
        "outlets": outlets, "teams": teams, "members": members,
    })


def form_detail_view(request, form_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_forms")
    if denied:
        return denied

    form = get_object_or_404(Form, id=form_id, organization=org)
    responses = FormResponse.objects.filter(form=form).select_related("submitted_by", "submitted_by__user")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update":
            form.title = request.POST.get("title", form.title)
            form.description = request.POST.get("description", form.description)
            form.status = request.POST.get("status", form.status)
            form.save()
            log_activity(org, profile, "updated", "form", form.id, form.title)
            return redirect("form_detail", form_id=form.id)

        elif action == "publish":
            form.status = "published"
            form.save(update_fields=["status"])
            log_activity(org, profile, "published", "form", form.id, form.title)
            return redirect("form_detail", form_id=form.id)

        elif action == "trash":
            form.status = "trashed"
            form.save(update_fields=["status"])
            log_activity(org, profile, "trashed", "form", form.id, form.title)
            return redirect("form_list")

    return render(request, "forms/detail.html", {
        "form": form, "responses": responses,
        "fields": form.fields_schema if form.fields_schema else [],
    })


def form_respond_view(request, form_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_forms")
    if denied:
        return denied

    form = get_object_or_404(Form, id=form_id, organization=org)

    if form.status != "published":
        return redirect("form_detail", form_id=form.id)

    if request.method == "POST":
        data = {}
        for field in (form.fields_schema or []):
            key = field.get("label", "")
            data[key] = request.POST.get(f"field_{key}", "")

        FormResponse.objects.create(
            form=form, submitted_by=profile, data=data, status="submitted"
        )
        log_activity(org, profile, "responded", "form", form.id, form.title)

        from notifications.models import Notification
        if form.created_by and form.created_by != profile:
            Notification.objects.create(
                organization=org, user=form.created_by,
                notification_type="form_response",
                title="New Form Response",
                message=f"{profile.full_name} responded to '{form.title}'",
                link=f"/forms/{form.id}/",
                entity_type="form", entity_id=form.id,
            )

        return redirect("form_detail", form_id=form.id)

    return render(request, "forms/respond.html", {
        "form": form,
        "fields": form.fields_schema if form.fields_schema else [],
    })


def form_response_detail_view(request, form_id, response_id):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "view_forms")
    if denied:
        return denied

    form = get_object_or_404(Form, id=form_id, organization=org)
    response = get_object_or_404(FormResponse, id=response_id, form=form)

    if request.method == "POST" and request.POST.get("action") == "review":
        response.status = "reviewed"
        response.reviewed_by = profile
        response.reviewed_at = timezone.now()
        response.save()
        return redirect("form_detail", form_id=form.id)

    return render(request, "forms/response_detail.html", {
        "form": form, "response": response,
        "fields": form.fields_schema if form.fields_schema else [],
    })

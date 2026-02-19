"""
Notifications app views.
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse

from core.views import get_current_org, get_current_profile, paginate
from .models import Notification


def notification_list_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")

    notifications = Notification.objects.filter(user=profile)
    notifications = paginate(notifications, request, 30)
    return render(request, "notifications/list.html", {"notifications": notifications})


def mark_all_read_view(request):
    profile = get_current_profile(request)
    if profile:
        Notification.objects.filter(user=profile, is_read=False).update(is_read=True)
    return redirect("notification_list")

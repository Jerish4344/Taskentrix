from core.models import Organization, Outlet, UserProfile


def global_context(request):
    """Add global context variables available in all templates."""
    context = {
        "organizations": Organization.objects.filter(is_active=True),
        "current_org_id": request.session.get("current_org_id"),
        "current_outlet_id": request.session.get("current_outlet_id"),
        "outlets": [],
        "user_profile": None,
        "unread_notifications": 0,
        "user_perms": {},
    }

    org_id = request.session.get("current_org_id")
    if org_id:
        context["outlets"] = Outlet.objects.filter(organization_id=org_id, is_active=True)

    user_id = request.session.get("user_id")
    if user_id:
        try:
            profile = UserProfile.objects.select_related(
                "user", "organization", "role", "outlet", "team"
            ).get(id=user_id)
            context["user_profile"] = profile
            from notifications.models import Notification
            context["unread_notifications"] = Notification.objects.filter(
                user=profile, is_read=False
            ).count()
            # Build permission lookup dict for templates
            if profile.role:
                perm_codes = profile.role.permissions.values_list("codename", flat=True)
                context["user_perms"] = {code: True for code in perm_codes}
        except UserProfile.DoesNotExist:
            pass

    return context

from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Organization / Outlet switching
    path("switch-org/<int:org_id>/", views.switch_organization, name="switch_org"),
    path("switch-outlet/<int:outlet_id>/", views.switch_outlet, name="switch_outlet"),
    path("clear-outlet/", views.clear_outlet, name="clear_outlet"),

    # Dashboard
    path("", views.dashboard_view, name="dashboard"),
    path("dashboard/", views.dashboard_view, name="dashboard_alt"),

    # Outlets
    path("outlets/", views.outlet_list_view, name="outlet_list"),
    path("outlets/create/", views.outlet_create_view, name="outlet_create"),
    path("outlets/<int:outlet_id>/edit/", views.outlet_edit_view, name="outlet_edit"),

    # Teams
    path("teams/", views.team_list_view, name="team_list"),
    path("teams/create/", views.team_create_view, name="team_create"),
    path("teams/<int:team_id>/edit/", views.team_edit_view, name="team_edit"),

    # Users
    path("users/", views.user_list_view, name="user_list"),
    path("users/create/", views.user_create_view, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit_view, name="user_edit"),

    # Roles
    path("roles/", views.role_list_view, name="role_list"),
    path("roles/create/", views.role_create_view, name="role_create"),
    path("roles/<int:role_id>/edit/", views.role_edit_view, name="role_edit"),

    # Activity Log
    path("activity/", views.activity_log_view, name="activity_log"),

    # API
    path("api/dashboard/", views.api_dashboard_data, name="api_dashboard"),
    path("api/notifications/", views.api_notifications, name="api_notifications"),
]

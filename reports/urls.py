from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_dashboard_view, name="reports_dashboard"),
    path("outlet-tasks/", views.report_outlet_tasks_view, name="report_outlet_tasks"),
    path("outlet-issues/", views.report_outlet_issues_view, name="report_outlet_issues"),
    path("employee-tasks/", views.report_employee_tasks_view, name="report_employee_tasks"),
    path("employee-issues/", views.report_employee_issues_view, name="report_employee_issues"),
    path("backlog/", views.report_backlog_view, name="report_backlog"),
    path("points/", views.report_points_view, name="report_points"),
    path("api/<str:report_type>/chart/", views.api_report_chart_data, name="api_report_chart"),
]

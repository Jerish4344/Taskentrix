from django.urls import path
from . import views

urlpatterns = [
    path("", views.issue_list_view, name="issue_list"),
    path("board/", views.issue_board_view, name="issue_board"),
    path("create/", views.issue_create_view, name="issue_create"),
    path("<int:issue_id>/", views.issue_detail_view, name="issue_detail"),
    path("api/<int:issue_id>/status/", views.api_issue_status_update, name="api_issue_status"),
]

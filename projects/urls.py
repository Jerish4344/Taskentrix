from django.urls import path
from . import views

urlpatterns = [
    path("", views.project_list_view, name="project_list"),
    path("board/", views.project_board_view, name="project_board"),
    path("create/", views.project_create_view, name="project_create"),
    path("<int:project_id>/", views.project_detail_view, name="project_detail"),
    path("api/<int:project_id>/status/", views.api_project_status_update, name="api_project_status"),
]

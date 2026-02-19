from django.urls import path
from . import views

urlpatterns = [
    path("", views.task_list_view, name="task_list"),
    path("board/", views.task_board_view, name="task_board"),
    path("calendar/", views.task_calendar_view, name="task_calendar"),
    path("create/", views.task_create_view, name="task_create"),
    path("<int:task_id>/", views.task_detail_view, name="task_detail"),
    path("api/<int:task_id>/status/", views.api_task_status_update, name="api_task_status"),
    path("api/<int:task_id>/star/", views.api_task_star_toggle, name="api_task_star"),
]

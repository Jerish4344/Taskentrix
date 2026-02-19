from django.urls import path
from . import views

urlpatterns = [
    path("", views.notification_list_view, name="notification_list"),
    path("mark-all-read/", views.mark_all_read_view, name="mark_all_read"),
]

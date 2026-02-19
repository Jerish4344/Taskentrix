from django.urls import path
from . import views

urlpatterns = [
    path("", views.template_library_view, name="template_library"),
    path("create/", views.template_create_view, name="template_create"),
    path("<int:template_id>/", views.template_detail_view, name="template_detail"),
    path("<int:template_id>/use/", views.template_use_view, name="template_use"),
]

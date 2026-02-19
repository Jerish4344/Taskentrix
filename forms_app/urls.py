from django.urls import path
from . import views

urlpatterns = [
    path("", views.form_list_view, name="form_list"),
    path("create/", views.form_create_view, name="form_create"),
    path("<int:form_id>/", views.form_detail_view, name="form_detail"),
    path("<int:form_id>/respond/", views.form_respond_view, name="form_respond"),
    path("<int:form_id>/response/<int:response_id>/", views.form_response_detail_view, name="form_response_detail"),
]

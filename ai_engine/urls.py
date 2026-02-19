from django.urls import path
from . import views

urlpatterns = [
    path("", views.ai_assistant_view, name="ai_assistant"),
    path("api/chat/", views.api_ai_chat, name="api_ai_chat"),
    path("api/suggest/", views.api_ai_suggest_tasks, name="api_ai_suggest"),
    path("api/priority/", views.api_ai_predict_priority, name="api_ai_priority"),
    path("api/delay/", views.api_ai_delay_prediction, name="api_ai_delay"),
    path("api/workload/", views.api_ai_workload_balance, name="api_ai_workload"),
    path("api/similarity/", views.api_ai_similarity_check, name="api_ai_similarity"),
]

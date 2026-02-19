"""
AI Engine views: assistant, predictions, suggestions.
"""
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import get_current_org, get_current_profile, require_perm
from core.ai_engine import AIEngine
from .models import AIAnalysis


def ai_assistant_view(request):
    org = get_current_org(request)
    profile = get_current_profile(request)
    if not org or not profile:
        return redirect("login")
    denied = require_perm(profile, "use_ai")
    if denied:
        return denied

    recent_analyses = AIAnalysis.objects.filter(organization=org)[:10]
    return render(request, "ai/assistant.html", {
        "recent_analyses": recent_analyses,
    })


@csrf_exempt
def api_ai_chat(request):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("use_ai"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            response = AIEngine.chat_response(message, org.name)

            AIAnalysis.objects.create(
                organization=org, analysis_type="summary",
                input_data={"message": message},
                result={"response": response},
                confidence=0.85,
            )
            return JsonResponse({"response": response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_ai_suggest_tasks(request):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("use_ai"):
            return JsonResponse({"error": "Permission denied"}, status=403)

        from tasks.models import Task
        existing = Task.objects.filter(organization=org, is_trashed=False)
        suggestions = AIEngine.suggest_tasks(org.name, existing)
        return JsonResponse({"suggestions": suggestions})
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_ai_predict_priority(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            result = AIEngine.predict_priority(data.get("title", ""), data.get("description", ""))
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_ai_delay_prediction(request):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("use_ai"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            data = json.loads(request.body)
            result = AIEngine.predict_delay(data)

            AIAnalysis.objects.create(
                organization=org, analysis_type="delay",
                input_data=data, result=result, confidence=result.get("confidence", 0.7),
            )
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_ai_workload_balance(request):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("use_ai"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            result = AIEngine.balance_workload(org)

            AIAnalysis.objects.create(
                organization=org, analysis_type="workload",
                input_data={"org_id": org.id}, result=result, confidence=0.8,
            )
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_ai_similarity_check(request):
    if request.method == "POST":
        org = get_current_org(request)
        profile = get_current_profile(request)
        if not org or not profile:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if not profile.has_perm("use_ai"):
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            data = json.loads(request.body)
            result = AIEngine.find_similar_tasks(org, data.get("title", ""), data.get("description", ""))
            return JsonResponse({"similar_tasks": result})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

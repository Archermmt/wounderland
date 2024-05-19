import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from wounderland.game import create_game, get_game
from .models import *

logger = logging.getLogger(__name__)


# Create your views here.
def village(request):
    user = request.session.get("user", "")
    context = {
        "agents": ["Isabella Rodriguez", "Klaus Mueller", "Maria Lopez"],
        "user": user,
    }
    if user and User.objects.filter(name=user):
        context["llm_keys"] = User.objects.get(name=user).all_llm_keys()
    else:
        context["llm_keys"] = []
    return render(request, "village/home.html", {"ctx": context})


@csrf_exempt
def start_game(request):
    if request.method == "POST":
        info = create_game(
            settings.STATICFILES_DIRS[0], json.loads(request.body), logger
        )
        return JsonResponse({"success": True, "info": info})
    return JsonResponse({"success": False, "error": "not a valid request"})


@csrf_exempt
def agent_think(request):
    game = get_game()
    if request.method == "POST" and game:
        info = game.agent_think(**json.loads(request.body))
        return JsonResponse({"success": True, "info": info})
    return JsonResponse({"success": True, "info": {"direct": "stop"}})


@csrf_exempt
def user_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if not data.get("name") or not data.get("password"):
            return JsonResponse({"success": False, "error": "missing user name"})
        request.session["user"] = data["name"]
        user, error = User.safe_get(data["name"], data["password"], data["email"])
        if not user:
            return JsonResponse({"success": False, "error": error})
        info = {"name": data["name"], "llm_keys": user.all_llm_keys()}
        return JsonResponse({"success": True, "info": info})
    return JsonResponse({"success": False, "error": "not a valid request"})


@csrf_exempt
def user_logout(request):
    user = request.session.get("user", "")
    request.session.pop("user")
    return JsonResponse({"success": True, "info": {"name": user}})


@csrf_exempt
def user_add_key(request):
    if request.method == "POST":
        user_name = request.session.get("user", "")
        if not user_name:
            return JsonResponse({"success": False, "error": "Can not find user"})
        data = json.loads(request.body)
        llm_key, error = LLMKey.safe_get(user_name, data["key"], data["value"])
        if not llm_key:
            return JsonResponse({"success": False, "error": error})
        info = {"user": user_name, "llm_keys": llm_key.user.all_llm_keys()}
        return JsonResponse({"success": True, "info": info})
    return JsonResponse({"success": False, "error": "not a valid request"})

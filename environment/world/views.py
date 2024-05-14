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
        return JsonResponse(
            create_game(settings.STATICFILES_DIRS[0], json.loads(request.body), logger)
        )
    return JsonResponse({"start": False})


@csrf_exempt
def agent_think(request):
    game = get_game()
    if request.method == "POST" and game:
        data = json.loads(request.body)
        plan = game.get_agent(data["name"]).think(data["status"])
        return JsonResponse(plan)
    return JsonResponse({"direct": "stop"})


@csrf_exempt
def user_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if not data.get("name") or not data.get("password"):
            return JsonResponse({"success": False, "error": "missing user name"})
        request.session["user"] = data["name"]
        user = User.objects.filter(name=data["name"])
        if user:
            user = user.first()
            if user.password != data.get("password"):
                return JsonResponse({"success": False, "error": "password mismatch"})
        else:
            user = User(
                name=data["name"], email=data["email"], password=data["password"]
            )
            user.save()
        return JsonResponse(
            {"success": True, "name": data["name"], "llm_keys": user.all_llm_keys()}
        )
    return JsonResponse({"success": False, "error": "not a valid request"})


@csrf_exempt
def user_logout(request):
    user = request.session.get("user", "")
    request.session.pop("user")
    return JsonResponse({"success": True, "name": user})


@csrf_exempt
def user_add_key(request):
    if request.method == "POST":
        user_name = request.session.get("user", "")
        if not user_name:
            return JsonResponse({"success": False, "error": "Can not find user"})
        user = User.objects.filter(name=user_name)
        if not user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Can not find user with name " + str(user_name),
                }
            )
        user, data = user.first(), json.loads(request.body)
        if not data.get("key") or not data.get("value"):
            return JsonResponse({"success": False, "error": "missing key or value"})
        llm_key = LLMKey.objects.filter(key=data["key"])
        if llm_key:
            llm_key.first().value = data["value"]
        else:
            llm_key = LLMKey(user=user, key=data["key"], value=data["value"])
        llm_key.save()
        return JsonResponse(
            {"success": True, "user": user_name, "llm_keys": user.all_llm_keys()}
        )
    return JsonResponse({"success": False, "error": "not a valid request"})

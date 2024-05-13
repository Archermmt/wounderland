import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from wounderland.game import create_game, get_game

logger = logging.getLogger(__name__)


# Create your views here.
def village(request):
    context = {"agents": ["Isabella Rodriguez", "Klaus Mueller", "Maria Lopez"]}
    return render(request, "village/home.html", context)


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
        if not data.get("name"):
            return JsonResponse({"success": False, "error": "missing user name"})
        print("has data " + str(data))
        return JsonResponse({"success": True, "name": data["name"]})
    return JsonResponse({"success": False, "error": "not a valid request"})

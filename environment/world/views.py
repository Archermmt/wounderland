import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from world.wounderland.game import create_game, get_game

logger = logging.getLogger(__name__)


# Create your views here.
def village(request):
    context = {"agents": ["Isabella Rodriguez", "Klaus Mueller", "Maria Lopez"]}
    return render(request, "village/home.html", context)


@csrf_exempt
def start_game(request):
    if request.method == "POST":
        return JsonResponse(
            create_game(settings.STATICFILES_DIRS[0], json.loads(request.body))
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

import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from wounderland.game import create_game, get_game
from wounderland.utils import set_timer, get_timer, create_io_logger, update_dict
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


def _get_user_config(user_name):
    if not user_name:
        return {}
    user, _ = User.safe_get(user_name)
    if not user:
        return {}
    return {
        "name": user.name,
        "keys": {k.key: k.value for k in user.llmkey_set.all()},
        "email": user.email,
    }


def _reset_user(user_name):
    game, config = get_game(), _get_user_config(user_name)
    if game and config:
        game.reset_user(**config)


def _remove_user():
    game = get_game()
    if game:
        game.remove_user()


@csrf_exempt
def start_game(request):
    if request.method == "POST":
        # TODO: use django logger
        logger = create_io_logger("info")
        data = json.loads(request.body)
        timer = set_timer(**data.get("time", {}))
        if data.get("keep_storage", True):
            for name in data["agents"]:
                data["agents"][name] = update_dict(
                    data["agents"][name], Agent.get_last(name, timer.get_date())
                )
        else:
            Agent.objects.all().delete()
        game = create_game(settings.STATICFILES_DIRS[0], data, logger=logger)
        _reset_user(request.session.get("user", ""))
        if not game:
            return JsonResponse({"success": False, "error": "failed to create game"})
        return JsonResponse({"success": True, "info": {"start": True}})
    return JsonResponse({"success": False, "error": "not a valid request"})


@csrf_exempt
def agent_think(request):
    game = get_game()
    if request.method == "POST" and game:
        info = game.agent_think(**json.loads(request.body))
        return JsonResponse({"success": True, "info": info})
    return JsonResponse(
        {"success": True, "info": {"name": "any", "path": [], "emojis": {}}}
    )


@csrf_exempt
def agent_save(request):
    game, timer = get_game(), get_timer()
    if request.method == "POST" and game:
        data = json.loads(request.body)
        agent_info = game.get_agent(data["name"]).to_dict(with_action=False)
        agent = Agent.from_dict(data["name"], timer.get_date(), **agent_info)
        return JsonResponse({"success": True, "info": {"name": agent.name}})
    return JsonResponse({"success": False, "error": "not a valid request"})


@csrf_exempt
def get_time(request):
    timer = get_timer()
    if request.method == "POST" and timer:
        data = json.loads(request.body)
        if data.get("offset"):
            timer.forward(data["offset"])
        if data.get("rate"):
            timer.speedup(data["rate"])
    return JsonResponse(
        {"success": True, "info": {"time": timer.get_date("%A %B %d %H:%M %p")}}
    )


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
        _reset_user(data["name"])
        info = {"name": data["name"], "llm_keys": user.all_llm_keys()}
        return JsonResponse({"success": True, "info": info})
    return JsonResponse({"success": False, "error": "not a valid request"})


@csrf_exempt
def user_logout(request):
    user = request.session.get("user", "")
    request.session.pop("user")
    _remove_user()
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
        _reset_user(user_name)
        return JsonResponse({"success": True, "info": info})
    return JsonResponse({"success": False, "error": "not a valid request"})

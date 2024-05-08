import json
import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from world.backend.reverie import ReverieServer

logger = logging.getLogger(__name__)


# Create your views here.
def village(request):
    context = {"agents": ["Isabella_Rodriguez", "Klaus_Mueller", "Maria_Lopez"]}
    return render(request, "village/home.html", context)


@csrf_exempt
def start_game(request):
    if request.method == "GET":
        return HttpResponse("Game Start")
    server = ReverieServer(json.loads(request.body))
    return HttpResponse("Game Over")

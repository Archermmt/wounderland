import json
from django.shortcuts import render


# Create your views here.
def village(request):
    context = {"agents": ["Abigail_Chen", "Adam_Smith", "Arthur_Burton"]}
    return render(request, "village/home.html", context)

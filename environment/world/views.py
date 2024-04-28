from django.shortcuts import render


# Create your views here.
def village(request):
    context = {"agents": ["Abigail_Chen", "Adam_Smith", "Arthur_Burton", "Ayesha_Khan"]}
    return render(request, "village/home.html", context)

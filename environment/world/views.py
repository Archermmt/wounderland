from django.shortcuts import render


# Create your views here.
def village(request):
    context = {}
    return render(request, "village/home.html", context)

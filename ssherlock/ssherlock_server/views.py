from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from .models import *


def landing(request):
    return render(request, "ssherlock_server/landing.html")


def home(request):
    return render(request, "ssherlock_server/home.html")


def target_servers(request):
    output = get_list_or_404(TargetServer.objects.all())
    return render(request, "ssherlock_server/target_servers.html", {"output": output})

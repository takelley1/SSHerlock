from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from .models import *
from .forms import *


def landing(request):
    return render(request, "ssherlock_server/landing.html")


def add_credential(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AddCredentialForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect("credential")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddCredentialForm()

    context = {"form": form, "object_name": "Credential"}
    return render(request, "ssherlock_server/objects/add_object.html", context)


def home(request):
    return render(request, "ssherlock_server/home.html")


def bastion_server_list(request):
    output = BastionServer.objects.all()
    context = {"output": output, "object_name": "Bastion Server"}
    return render(request, "ssherlock_server/objects/object.html", context)


def credential_list(request):
    output = Credential.objects.all()
    context = {"output": output, "object_name": "Credential"}
    return render(request, "ssherlock_server/objects/object.html", context)


def job_list(request):
    output = Job.objects.all()
    context = {"output": output, "object_name": "Job"}
    return render(request, "ssherlock_server/objects/object.html", context)


def llm_api_list(request):
    output = LlmApi.objects.all()
    context = {"output": output, "object_name": "LLM API"}
    return render(request, "ssherlock_server/objects/object.html", context)


def target_server_list(request):
    output = TargetServer.objects.all()
    context = {"output": output, "object_name": "Target Server"}
    return render(request, "ssherlock_server/objects/object.html", context)

"""All Django views for the SSHerlock server application."""
from django.shortcuts import get_list_or_404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import BastionHostForm
from .forms import CredentialForm
from .forms import TargetHostForm
from .models import BastionHost
from .models import Credential
from .models import Job
from .models import LlmApi
from .models import TargetHost


def landing(request):
    """Get the landing page."""
    return render(request, "ssherlock_server/landing.html")


# Allows us to get the model object matching the string passed to the handle_object function.
MODEL_FORM_MAP = {
    "credential": (Credential, CredentialForm),
    "bastion_host": (BastionHost, BastionHostForm),
    "target_host": (TargetHost, TargetHostForm),
}


def handle_object(request, model_type, uuid=None):
    """Handle creating or editing any object."""
    # Get the model, form, and template based on the model_type parameter
    model, form = MODEL_FORM_MAP.get(model_type)

    if not model or not form:
        # Handle the case where the model_type is not valid
        return render(request, "404.html", status=404)

    instance = None
    if uuid:
        instance = get_object_or_404(model, pk=uuid)

    form = form(request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/{model_type}")

    context = {
        "form": form,
        "object_name": "Credential",
        "uuid": uuid,
    }
    if uuid:
        template_name = "ssherlock_server/objects/edit_object.html"
    else:
        template_name = "ssherlock_server/objects/add_object.html"
    return render(request, template_name, context)


def home(request):
    """Return the home page after a user has logged in."""
    return render(request, "ssherlock_server/home.html")


def bastion_host_list(request):
    """List the bastion hosts."""
    output = BastionHost.objects.all()
    context = {"output": output, "object_name": "Bastion Host"}
    return render(request, "ssherlock_server/objects/object.html", context)


def credential_list(request):
    """List the credentials."""
    output = Credential.objects.all()
    context = {"output": output, "object_name": "Credential"}
    return render(request, "ssherlock_server/objects/credential.html", context)


def job_list(request):
    """List all jobs."""
    output = Job.objects.all()
    context = {"output": output, "object_name": "Job"}
    return render(request, "ssherlock_server/objects/object.html", context)


def llm_api_list(request):
    """List the LLM APIs."""
    output = LlmApi.objects.all()
    context = {"output": output, "object_name": "LLM API"}
    return render(request, "ssherlock_server/objects/object.html", context)


def target_host_list(request):
    """List the target hosts."""
    output = TargetHost.objects.all()
    context = {"output": output, "object_name": "Target Host"}
    return render(request, "ssherlock_server/objects/object.html", context)

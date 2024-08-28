"""All Django views for the SSHerlock server application."""
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import BastionHostForm
from .forms import CredentialForm
from .forms import JobForm
from .forms import LlmApiForm
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
    "llm_api": (LlmApi, LlmApiForm),
    "job": (Job, JobForm),
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
        "object_name": model_type.capitalize(),
        "uuid": uuid,
    }
    if uuid:
        template_name = "ssherlock_server/objects/edit_object.html"
    else:
        template_name = "ssherlock_server/objects/add_object.html"
    return render(request, template_name, context)


def delete_object(request, model_type, uuid):
    """Delete the given object."""
    # Get the model, form, and template based on the model_type parameter
    model, form = MODEL_FORM_MAP.get(model_type)

    if not model or not form:
        # Handle the case where the model_type is not valid
        return render(request, "404.html", status=404)

    instance = get_object_or_404(model, pk=uuid)

    instance.delete()
    return redirect(f"/{model_type}")


def home(request):
    """Return the home page after a user has logged in."""
    return render(request, "ssherlock_server/home.html")


def bastion_host_list(request):
    """List the bastion hosts."""
    output = BastionHost.objects.all()
    column_headers = ["Hostname"]
    object_fields = ["hostname"]
    object_name = "Bastion Host"
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "ssherlock_server/objects/object_list.html", context)


def credential_list(request):
    """List the credentials."""
    output = Credential.objects.all()
    column_headers = ["Name", "Username", "Password"]
    object_fields = ["credential_name", "username", "password"]
    object_name = "Credential"
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "ssherlock_server/objects/object_list.html", context)

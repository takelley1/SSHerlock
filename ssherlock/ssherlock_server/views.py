"""All Django views for the SSHerlock server application."""
# pylint: disable=import-error
from django.http import Http404
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
    """Handle creating or editing any object except jobs."""
    # Get the model, form, and template based on the model_type parameter
    try:
        model, form = MODEL_FORM_MAP.get(model_type)
    except TypeError:
        raise Http404("Model type not found.")

    instance = None
    if uuid:
        instance = get_object_or_404(model, pk=uuid)

    form = form(request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/{model_type}_list")

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
    try:
        model, form = MODEL_FORM_MAP.get(model_type)
    except TypeError:
        raise Http404("Model type not found.")

    instance = get_object_or_404(model, pk=uuid)

    instance.delete()
    return redirect(f"/{model_type}_list")


def create_job(request):
    """Handle creating jobs.

    When the create job form is submitted, a new job is created for every target host.
    """
    form = JobForm(request.POST)

    if request.method == "POST" and form.is_valid():

        cleaned_data = form.cleaned_data
        # Get list of target hosts and also remove the list of target hosts from the cleaned data.
        target_hosts = cleaned_data.pop("target_hosts", [])

        for host in target_hosts:
            # Copy all the attributes from cleaned data into the job (excluding target hosts).
            job = Job(**cleaned_data)
            # Save the job object to create a primary key.
            job.save()
            # Add the single host to each job that's created.
            job.target_hosts.add(host.id)
            job.save()

        return redirect("/job_list")

    context = {
        "form": form,
        "object_name": "Job",
    }
    template_name = "ssherlock_server/objects/add_object.html"
    return render(request, template_name, context)


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


def llm_api_list(request):
    """List the LLM APIs."""
    output = LlmApi.objects.all()
    column_headers = ["Base URL", "API Key"]
    object_fields = ["base_url", "api_key"]
    object_name = "LLM API"
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "ssherlock_server/objects/object_list.html", context)


def job_list(request):
    """List the jobs."""
    output = Job.objects.all()

    column_headers = [
        "Status",
        "LLM API",
        "Target Hosts",
        "Target Host Credentials",
    ]
    object_fields = [
        "status",
        "llm_api",
        "target_hosts",
        "credentials_for_target_hosts",
    ]

    # Add only the necessary column headers since some fields are not always populated.
    # If any output obejct has one of these fields, add it to the column headers.
    for item in output:
        if item.bastion_host:
            object_fields.append("bastion_host")
            column_headers.append("Bastion Host")
            break
    for item in output:
        if item.credentials_for_bastion_host:
            column_headers.append("Bastion Host Credentials")
            object_fields.append("credentials_for_bastion_host")
            break

    object_name = "Job"
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "ssherlock_server/objects/object_list.html", context)


def target_host_list(request):
    """List the target hosts."""
    output = TargetHost.objects.all()
    column_headers = ["Hostname"]
    object_fields = ["hostname"]
    object_name = "Target Host"
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "ssherlock_server/objects/object_list.html", context)

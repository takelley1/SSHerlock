"""All Django views for the SSHerlock server application."""

# pylint: disable=import-error, missing-class-docstring, missing-function-docstring, invalid-str-returned, no-member, invalid-name, unused-argument

import json
from django.http import Http404, JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect, render
from .forms import BastionHostForm, CredentialForm, JobForm, LlmApiForm, TargetHostForm
from .models import BastionHost, Credential, Job, LlmApi, TargetHost
from .utils import check_private_key


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
    model_form_tuple = MODEL_FORM_MAP.get(model_type)
    if not model_form_tuple:
        raise Http404("Model type not found.")

    model, form_class = model_form_tuple
    instance = get_object_or_404(model, pk=uuid) if uuid else None
    form = form_class(request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/{model_type}_list")

    context = {
        "form": form,
        "object_name": model_type.capitalize(),
        "uuid": uuid,
    }
    template_name = (
        "ssherlock_server/objects/edit_object.html"
        if uuid
        else "ssherlock_server/objects/add_object.html"
    )
    return render(request, template_name, context)


def delete_object(request, model_type, uuid):
    """Delete the given object."""
    model_form_tuple = MODEL_FORM_MAP.get(model_type)
    if not model_form_tuple:
        raise Http404("Model type not found.")

    model, _ = model_form_tuple
    instance = get_object_or_404(model, pk=uuid)
    instance.delete()
    return redirect(f"/{model_type}_list")


def create_job(request):
    """Handle creating jobs. When the create job form is submitted, a new job is created for every target host."""
    form = JobForm(request.POST)
    if request.method == "POST" and form.is_valid():
        cleaned_data = form.cleaned_data
        target_hosts = cleaned_data.pop("target_hosts", [])

        for host in target_hosts:
            job = Job(**cleaned_data)
            job.save()
            job.target_hosts.add(host.id)
            job.save()

        return redirect("/job_list")

    context = {
        "form": form,
        "object_name": "Job",
    }
    return render(request, "ssherlock_server/objects/add_object.html", context)


def home(request):
    """Return the home page after a user has logged in."""
    return render(request, "ssherlock_server/home.html")


def bastion_host_list(request):
    """List the bastion hosts."""
    return render_object_list(
        request, BastionHost, ["Hostname", "Port"], ["hostname", "port"], "Bastion Host"
    )


def credential_list(request):
    """List the credentials."""
    return render_object_list(
        request,
        Credential,
        ["Name", "Username", "Password"],
        ["credential_name", "username", "password"],
        "Credential",
    )


def llm_api_list(request):
    """List the LLM APIs."""
    return render_object_list(
        request, LlmApi, ["Base URL", "API Key"], ["base_url", "api_key"], "LLM API"
    )


def job_list(request):
    """List the jobs."""
    return render_object_list(
        request,
        Job,
        ["Status", "LLM API", "Target Hosts", "Target Host Credentials"],
        ["status", "llm_api", "target_hosts", "credentials_for_target_hosts"],
        "Job",
    )


def target_host_list(request):
    """List the target hosts."""
    return render_object_list(
        request, TargetHost, ["Hostname", "Port"], ["hostname", "port"], "Target Host"
    )


def render_object_list(request, model, column_headers, object_fields, object_name):
    """Helper function to render object lists."""
    output = model.objects.all()
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "ssherlock_server/objects/object_list.html", context)


@require_http_methods(["GET"])
def request_job(request):
    """Provide a job for runners to process. This is the API endpoint used by runners to retrieve a job."""
    try:
        key_check_response = check_private_key(request)
        if key_check_response:
            return key_check_response

        job = Job.objects.filter(status="PENDING").order_by("created_at").first()
        if not job:
            return JsonResponse({"message": "No pending jobs found."}, status=404)
        return JsonResponse(job.dict(), status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@require_http_methods(["POST"])
def update_job_status(request, job_id):
    """Update the status of a job. This is the API endpoint used by runners to update the status of a job."""
    try:
        key_check_response = check_private_key(request)
        if key_check_response:
            return key_check_response

        data = json.loads(request.body)
        new_status = data.get("status")
        if not new_status:
            return JsonResponse({"message": "Status not provided."}, status=400)

        job = get_object_or_404(Job, pk=job_id)
        job.status = new_status
        job.save()

        return HttpResponse(status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

"""All Django views for the SSHerlock server application."""

# pylint: disable=import-error, missing-class-docstring, missing-function-docstring, invalid-str-returned, no-member, invalid-name, unused-argument

import json
import os
from django.http import Http404, JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.utils import timezone
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
    # Reload the page that this function was called from to reflect the change.
    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return redirect(referer_url)
    else:
        # Fallback URL if HTTP_REFERER is not set
        return redirect(f"/{model_type}_list")


def retry_job(request, job_id):
    """Changes a given job's status to 'Pending.'"""
    job = get_object_or_404(Job, pk=job_id)
    if job.status in ["Failed", "Canceled"]:
        job.status = "Pending"
        job.save()
    # Reload the page that this function was called from to reflect the change.
    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return redirect(referer_url)
    else:
        # Fallback URL if HTTP_REFERER is not set
        return redirect('/job_list')


def cancel_job(request, job_id):
    """Cancel a given job by changing its status to 'Canceled.'"""
    job = get_object_or_404(Job, pk=job_id)
    if job.status not in ["Completed", "Canceled"]:
        job.status = "Canceled"
        job.save()
    # Reload the page that this function was called from to reflect the change.
    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return redirect(referer_url)
    else:
        # Fallback URL if HTTP_REFERER is not set
        return redirect('/job_list')


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


def view_job(request, job_id):
    """View details for a given job, including the job log"""
    job = get_object_or_404(Job, pk=job_id)
    context = {
        "job": job,
    }
    return render(request, "ssherlock_server/objects/view_job.html", context)


def home(request):
    """Return the home page after a user has logged in."""
    return render(request, "ssherlock_server/home.html")


def bastion_host_list(request):
    """List the bastion hosts."""
    return render_object_list(
        request,
        BastionHost,
        ["Creation", "Hostname", "Port"],
        ["created_at", "hostname", "port"],
        "Bastion Host",
    )


def credential_list(request):
    """List the credentials."""
    return render_object_list(
        request,
        Credential,
        ["Creation", "Name", "Username", "Password"],
        ["created_at", "credential_name", "username", "password"],
        "Credential",
    )


def llm_api_list(request):
    """List the LLM APIs."""
    return render_object_list(
        request,
        LlmApi,
        ["Creation", "Base URL", "API Key"],
        ["created_at", "base_url", "api_key"],
        "LLM API",
    )


def job_list(request):
    """List the jobs."""
    return render_object_list(
        request,
        Job,
        [
            "Creation",
            "Status",
            "LLM API",
            "Bastion Host",
            "Bastion Host Credentials",
            "Target Host",
            "Target Host Credentials",
        ],
        [
            "created_at",
            "status",
            "llm_api",
            "bastion_host",
            "credentials_for_bastion_host",
            "target_hosts_str",
            "credentials_for_target_hosts",
        ],
        "Job",
    )


def target_host_list(request):
    """List the target hosts."""
    return render_object_list(
        request,
        TargetHost,
        ["Creation", "Hostname", "Port"],
        ["created_at", "hostname", "port"],
        "Target Host",
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
@csrf_exempt
def request_job(request):
    """Provide a job for runners to process. This is the API endpoint used by runners to retrieve a job."""
    try:
        key_check_response = check_private_key(request)
        if key_check_response:
            return key_check_response

        job = Job.objects.filter(status="Pending").order_by("created_at").first()
        if not job:
            return JsonResponse({"message": "No pending jobs found."}, status=404)
        return JsonResponse(job.dict(), status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
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

        VALID_STATUSES = [
            "Canceled",
            "Completed",
            "Context Exceeded",
            "Failed",
            "Pending",
            "Running",
        ]
        if new_status not in VALID_STATUSES:
            return JsonResponse(
                {"message": f"Invalid status: {new_status}"}, status=400
            )

        job = get_object_or_404(Job, pk=job_id)
        job.status = new_status

        if new_status == "Running":
            job.started_at = timezone.now()
        elif new_status == "Completed":
            job.completed_at = timezone.now()

        job.save()

        return HttpResponse(status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def get_job_status(request, job_id):
    """Get the status of a job. This is the API endpoint used by runners."""
    try:
        key_check_response = check_private_key(request)
        if key_check_response:
            return key_check_response

        job = get_object_or_404(Job, pk=job_id)
        return JsonResponse({"status": str(job.status)}, status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def log_job_data(request, job_id):
    """Receive log data from the runners and write it to a file based on job_id."""
    try:
        # Check for valid authorization key
        key_check_response = check_private_key(request)
        if key_check_response:
            return key_check_response

        # Parse the incoming JSON data
        data = json.loads(request.body)
        log_content = data.get("log")

        if not log_content:
            return JsonResponse({"message": "Log content not provided."}, status=400)

        # Define the directory and file path for storing logs.
        # Use the .git/objects method of storing job files.
        # The first two characters of the job ID become a subdirectory.
        # The next two characters of the job ID become another subdirectory.
        # The remainining characters of the job ID become the name of the log file.
        # This is to prevent letting directories fill up with tons of files.
        job_id = str(job_id)
        log_dir = os.path.join(
            settings.BASE_DIR.parent,
            "ssherlock_runner_job_logs",
            job_id[0:2],
            job_id[2:4],
            job_id[4:6],
        )

        os.makedirs(log_dir, exist_ok=True)

        log_file_path = os.path.join(log_dir, f"{job_id[6:]}.log")

        # Write the log data to the file
        with open(log_file_path, "a", encoding="utf-8", buffering=1) as log_file:
            log_file.write(log_content + "\n")

        return HttpResponse(status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

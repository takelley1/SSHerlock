"""All Django views for the SSHerlock server application."""

# pylint: disable=import-error, invalid-str-returned, no-member

import json
import os
import time
import datetime

from django.conf import settings
from django.contrib.auth import (
    login,
    update_session_auth_hash,
    password_validation,
    logout,
)
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.http import (
    Http404,
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import (
    CustomUserCreationForm,
    BastionHostForm,
    CredentialForm,
    JobForm,
    LlmApiForm,
    TargetHostForm,
)
from .models import BastionHost, Credential, Job, LlmApi, TargetHost
from .utils import (
    check_private_key,
    get_object_pretty_name,
    get_job_log_path,
    read_full_job_log,
    stream_job_log_generator,
)


def landing(request):
    """Get the landing page."""
    return render(request, "landing.html")


# Allows us to get the model object matching the string passed to the handle_object function.
MODEL_FORM_MAP = {
    "credential": (Credential, CredentialForm),
    "llm_api": (LlmApi, LlmApiForm),
    "job": (Job, JobForm),
    "bastion_host": (BastionHost, BastionHostForm),
    "target_host": (TargetHost, TargetHostForm),
}


@login_required
def handle_object(request, model_type, uuid=None):
    """Handle creating or editing any object except jobs."""
    model_form_tuple = MODEL_FORM_MAP.get(model_type)
    if not model_form_tuple:
        raise Http404("Model type not found.")

    model, form_class = model_form_tuple
    instance = get_object_or_404(model, pk=uuid) if uuid else None
    form = form_class(request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        # Use the currently-logged-in user in the user field of the object.
        obj.user = request.user
        obj.save()
        return redirect(f"/{model_type}_list")

    context = {
        "object_name_pretty": get_object_pretty_name(model_type),
        "form": form,
        "object_name": model_type.capitalize(),
        "uuid": uuid,
    }
    template_name = "objects/edit_object.html" if uuid else "objects/add_object.html"
    return render(request, template_name, context)


@login_required
def delete_object(request, model_type, uuid):
    """Delete the given object."""
    model_form_tuple = MODEL_FORM_MAP.get(model_type)
    if not model_form_tuple:
        raise Http404("Model type not found.")

    model, _ = model_form_tuple
    instance = get_object_or_404(model, pk=uuid)
    instance.delete()
    # Reload the page that this function was called from to reflect the change.
    referer_url = request.META.get("HTTP_REFERER")
    if referer_url:
        return redirect(referer_url)
    # Fallback URL if HTTP_REFERER is not set.
    return redirect(f"/{model_type}_list")


@login_required
def retry_job(request, job_id):
    """Changes a given job's status to Pending."""
    job = get_object_or_404(Job, pk=job_id)
    if job.status in ["Failed", "Canceled"]:
        job.status = "Pending"
        job.save()
    # Reload the page that this function was called from to reflect the change.
    referer_url = request.META.get("HTTP_REFERER")
    if referer_url:
        return redirect(referer_url)
    # Fallback URL if HTTP_REFERER is not set.
    return redirect("/job_list")


@login_required
def cancel_job(request, job_id):
    """Cancel a given job by changing its status to Canceled."""
    job = get_object_or_404(Job, pk=job_id)
    if job.status not in ["Completed", "Canceled"]:
        job.status = "Canceled"
        job.save()
    # Reload the page that this function was called from to reflect the change.
    referer_url = request.META.get("HTTP_REFERER")
    if referer_url:
        return redirect(referer_url)
    # Fallback URL if HTTP_REFERER is not set.
    return redirect("/job_list")


@login_required
def create_job(request):
    """Handle creating jobs. When the create job form is submitted, a new job is created for every target host."""
    form = JobForm(request.POST)
    if request.method == "POST" and form.is_valid():
        cleaned_data = form.cleaned_data
        target_hosts = cleaned_data.pop("target_hosts", [])

        for host in target_hosts:
            # Use the currently-logged-in user in the user field of the object.
            job = Job(user=request.user, **cleaned_data)
            job.save()
            job.target_hosts.add(host.id)
            job.save()

            # Create an empty log file for this job so SSE consumers won't immediately
            # encounter "file not found" when the stream is opened right after creation.
            try:
                log_dir, log_file_path = get_job_log_path(job.id)
                os.makedirs(log_dir, exist_ok=True)
                open(log_file_path, "a", encoding="utf-8").close()
            except Exception:
                pass

        # Start a SSHerlock runner Docker container in GCP for every target host
        # in the job.
        # for host in target_hosts:
        #     gcp.run()

        return redirect("/job_list")

    context = {
        "form": form,
        "object_name": "Job",
        "object_name_pretty": "Job",
    }
    return render(request, "objects/add_object.html", context)


@login_required
def view_job(request, job_id):
    """View details for a given job, including the job log."""
    job = get_object_or_404(Job, pk=job_id)
    context = {
        "job": job,
    }
    return render(request, "objects/view_job.html", context)


@require_http_methods(["GET"])
@login_required
def get_full_job_log(request, job_id):
    """Return the full job log as plain text."""
    content = read_full_job_log(job_id)
    return HttpResponse(content, content_type="text/plain")


@login_required
def stream_job_log(request, job_id):
    """Stream job log data to the client using utils.stream_job_log_generator."""
    return StreamingHttpResponse(
        stream_job_log_generator(job_id), content_type="text/event-stream"
    )


def custom_login(request):
    """Render the login page and handle user authentication."""
    form = AuthenticationForm(request, data=request.POST or None)
    error_message = None

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                error_message = "Invalid username or password."
        else:
            error_message = "Invalid username or password."

    return render(request, "login.html", {"form": form, "error_message": error_message})


def signup(request):
    """Render the signup page and handle user registration."""
    form = CustomUserCreationForm(request.POST or None)
    error_message = None
    if request.method == "POST":
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect("home")
            except ValidationError as e:
                error_message = "\n".join(e.messages)
        else:
            error_message = "\n".join(
                [error for field, errors in form.errors.items() for error in errors]
            )

    return render(
        request, "signup.html", {"form": form, "error_message": error_message}
    )


@login_required
def home(request):
    """Return the home page after a user has logged in."""
    return render(request, "home.html")


@login_required
def bastion_host_list(request):
    """List the bastion hosts."""
    return render_object_list(
        request,
        BastionHost,
        ["Creation", "Hostname", "Port"],
        ["created_at", "hostname", "port"],
        "Bastion Host",
    )


@login_required
def credential_list(request):
    """List the credentials."""
    return render_object_list(
        request,
        Credential,
        ["Creation", "Name", "Username", "Password"],
        ["created_at", "credential_name", "username", "password"],
        "Credential",
    )


@login_required
def llm_api_list(request):
    """List the LLM APIs."""
    return render_object_list(
        request,
        LlmApi,
        ["Creation", "Base URL", "API Key"],
        ["created_at", "base_url", "api_key"],
        "LLM API",
    )


@login_required
def job_list(request):
    """List the jobs."""
    output = Job.objects.filter(user=request.user)
    context = {
        "output": output,
        "column_headers": [
            "Creation",
            "Status",
            "LLM API",
            "Target Host",
            "Target Host Credentials",
        ],
        "object_name": "Job",
        "object_fields": [
            "created_at",
            "status",
            "llm_api",
            "target_hosts_str",
            "credentials_for_target_hosts",
        ],
    }
    return render(request, "objects/job_list.html", context)


@login_required
def target_host_list(request):
    """List the target hosts."""
    return render_object_list(
        request,
        TargetHost,
        ["Creation", "Hostname", "Port"],
        ["created_at", "hostname", "port"],
        "Target Host",
    )


@login_required
def render_object_list(request, model, column_headers, object_fields, object_name):
    """Helper function to render object lists."""
    output = model.objects.filter(user=request.user)
    context = {
        "output": output,
        "column_headers": column_headers,
        "object_name": object_name,
        "object_fields": object_fields,
    }
    return render(request, "objects/object_list.html", context)


@require_http_methods(["GET"])
@csrf_exempt
def request_job(request):
    """Provide a job for runners to process.

    This is the API endpoint used by runners to retrieve a job.
    """
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

        valid_statuses = [
            "Canceled",
            "Completed",
            "Context Exceeded",
            "Failed",
            "Pending",
            "Running",
        ]
        if new_status not in valid_statuses:
            return JsonResponse(
                {"message": f"Invalid status: {new_status}"}, status=400
            )

        job = get_object_or_404(Job, pk=job_id)
        job.status = new_status

        # Also update timestamps accordingly.
        if new_status == "Running":
            job.started_at = timezone.now()
        elif new_status == "Completed":
            job.completed_at = timezone.now()
        elif new_status == "Failed":
            job.stopped_at = timezone.now()

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

        job_id = str(job_id)
        log_dir, log_file_path = get_job_log_path(job_id)
        os.makedirs(log_dir, exist_ok=True)

        # Write the log data to the file with a UTC timestamp prefix.
        timestamp = (
            timezone.now()
            .astimezone(datetime.timezone.utc)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        with open(log_file_path, "a", encoding="utf-8", buffering=1) as log_file:
            log_file.write(f"{timestamp} {log_content}\n")

        return HttpResponse(status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@login_required
def account(request):
    """Render the account page."""
    return render(
        request,
        "account.html",
        {"success": request.GET.get("success"), "error": request.GET.get("error")},
    )


@login_required
def update_email(request):
    """Handle email update for the user."""
    if request.method == "POST":
        new_email = request.POST.get("new_email")
        if new_email:
            try:
                request.user.email = new_email
                request.user.save()
                return redirect(
                    f"{reverse('account')}?success=Email successfully updated."
                )
            except Exception as e:
                email_error = str(e)
        else:
            email_error = "Email cannot be empty."
    return render(request, "account.html", {"email_error": email_error})


@login_required
def reset_password(request):
    """Handle password reset for the user."""
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password and new_password == confirm_password:
            try:
                # Validate the new password
                password_validation.validate_password(new_password, request.user)
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(
                    request, request.user
                )  # Keep the user logged in
                return render(
                    request,
                    "account.html",
                    {"success": "Password successfully changed."},
                )
            except ValidationError as e:
                error = "\n".join(e.messages)
        elif new_password and new_password != confirm_password:
            error = "Passwords do not match."
        else:
            error = "Unknown error."
    return render(request, "account.html", {"error": error})


@login_required
def delete_account(request):
    """Handle account deletion for the user."""
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        return redirect("landing")

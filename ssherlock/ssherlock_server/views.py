"""All Django views for the SSHerlock server application."""

# pylint: disable=import-error
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
    except TypeError as exc:
        raise Http404("Model type not found.") from exc

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


def delete_object(request, model_type, uuid):  # pylint: disable=unused-argument
    """Delete the given object."""
    # Get the model, form, and template based on the model_type parameter
    try:
        model, _ = MODEL_FORM_MAP.get(model_type)
    except TypeError as exc:
        raise Http404("Model type not found.") from exc

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
            job.target_hosts.add(host.id)  # pylint: disable=no-member
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
    output = BastionHost.objects.all()  # pylint: disable=no-member
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
    output = Credential.objects.all()  # pylint: disable=no-member
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
    output = LlmApi.objects.all()  # pylint: disable=no-member
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
    output = Job.objects.all()  # pylint: disable=no-member

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
    output = TargetHost.objects.all()  # pylint: disable=no-member
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


@require_http_methods(["GET"])
def request_job(request):  # pylint: disable=unused-argument
    """
    Provide a job for runners to process.

    This is the API endpoint used by runners to retrieve a job.
    """
    try:
        # Only return data if the correct private key is in the header.
        private_key = request.headers.get('Private-Key')
        if not private_key:
            return JsonResponse({"message": "Private key not provided."}, status=404)
        elif private_key != "myprivatekey":
            return JsonResponse({"message": "Private key incorrect."}, status=404)

        # Query the oldest pending job
        job = (
            Job.objects.filter(status="PENDING").order_by("created_at").first()
        )  # pylint: disable=no-member

        if job is None:
            return JsonResponse({"message": "No pending jobs found."}, status=404)

        # Use getattr here since some fields may not have values.
        job_data = {
            "id": str(job.id),
            "llm_api_baseurl": getattr(job.llm_api, "base_url", None),
            "llm_api_api_key": getattr(job.llm_api, "api_key", None),
            "bastion_host_hostname": getattr(job.bastion_host, "hostname", None),
            "bastion_host_port": getattr(job.bastion_host, "port", None),
            "credentials_for_bastion_host_username": getattr(
                job.credentials_for_bastion_host, "username", None
            ),
            "credentials_for_bastion_host_password": getattr(
                job.credentials_for_bastion_host, "password", None
            ),
            "target_host_hostname": getattr(
                job.target_hosts.all()[0], "hostname", None
            ),
            "target_host_port": getattr(job.target_hosts.all()[0], "port", None),
            "credentials_for_target_hosts_username": getattr(
                job.credentials_for_target_hosts, "username", None
            ),
            "credentials_for_target_hosts_password": getattr(
                job.credentials_for_target_hosts, "password", None
            ),
            "instructions": job.instructions,
        }

        return JsonResponse(job_data, status=200)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

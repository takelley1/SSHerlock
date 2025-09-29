"""Miscellaneous utility functions."""

from django.http import JsonResponse
import os
from django.conf import settings
from typing import Tuple


def check_private_key(request):
    """Check if the correct private key is provided in the request headers.

    Returns:
        JsonResponse or None: Returns a JsonResponse on error, otherwise None.
    """
    authorization_header = request.headers.get("Authorization")
    if not authorization_header:
        return JsonResponse(
            {"message": "Authorization header not provided."}, status=400
        )
    if not authorization_header.startswith("Bearer "):
        return JsonResponse(
            {"message": "Invalid Authorization header format."}, status=400
        )

    token = authorization_header.split(" ")[1]
    if token != "myprivatekey":
        return JsonResponse({"message": "Authorization token incorrect."}, status=404)
    return None


def get_object_pretty_name(model_type):
    """Convert a model type string to a pretty name."""
    if model_type == "llm_api" or model_type == "LLM API":
        pretty_name = "LLM API"
    else:
        pretty_name = model_type.replace("_", " ").title()
    return pretty_name


def get_job_log_path(job_id: str) -> Tuple[str, str]:
    """Return the log directory and log file path for a given job ID.

    Args:
        job_id (str): The UUID (or string) of the job.

    Returns:
        tuple: (log_dir, log_file_path)
    """
    job_id = str(job_id)
    log_dir = os.path.join(
        settings.BASE_DIR.parent,
        "ssherlock_runner_job_logs",
        job_id[0:2],
        job_id[2:4],
        job_id[4:6],
    )
    log_file_path = os.path.join(log_dir, f"{job_id[6:]}.log")
    return log_dir, log_file_path

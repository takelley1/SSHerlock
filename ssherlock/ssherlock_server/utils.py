"""Miscellaneous utility functions."""

from django.http import JsonResponse
import os
import time
from django.conf import settings
from typing import Tuple, Iterator


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
    log_file_path = os.path.join(log_dir, f"{job_id[6:]}.log")
    return log_dir, log_file_path


def read_full_job_log(job_id: str) -> str:
    """Read and return the full contents of a job log file.

    If the log file does not exist, return an empty string.

    Args:
        job_id (str): The UUID (or string) of the job.

    Returns:
        str: The entire log file contents or an empty string.
    """
    _, log_file_path = get_job_log_path(job_id)
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def stream_job_log_generator(job_id: str) -> Iterator[str]:
    """Generator that yields Server-Sent Events for new job log lines.

    The generator seeks to the end of the current log file and yields any new
    lines appended to the file. If the file is missing it yields a single
    SSE-formatted error event.

    Args:
        job_id (str): The UUID (or string) of the job.

    Yields:
        Iterator[str]: SSE-formatted strings to be sent over a text/event-stream.
    """
    _, log_file_path = get_job_log_path(job_id)
    try:
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            # Move to the end of the file so we only stream new lines.
            log_file.seek(0, os.SEEK_END)
            while True:
                line = log_file.readline()
                if line:
                    # SSE data lines must not contain bare newlines other than
                    # the delimiter between events.
                    yield f"data: {line}\n\n"
                else:
                    time.sleep(1)
    except FileNotFoundError:
        yield (f"event: error\ndata: Log file not found for job ID {job_id}.\n\n")

"""Miscellaneous utility functions."""

from django.http import JsonResponse


def check_private_key(request):
    """Check if the correct private key is provided in the request headers."""
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
    if model_type == "llm_api":
        pretty_name = "LLM API"
    else:
        pretty_name = model_type.replace("_", " ").title()
    return pretty_name

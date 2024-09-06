"""Miscellaneous utility functions."""

from django.http import JsonResponse


def check_private_key(request):
    """
    Check if the correct private key is provided in the request headers.
    """
    authorization_header = request.headers.get("Authorization")
    if not authorization_header:
        return JsonResponse({"message": "Authorization header not provided."}, status=404)
    if not authorization_header.startswith("Bearer "):
        return JsonResponse({"message": "Invalid Authorization header format."}, status=400)

    token = authorization_header.split(" ")[1]
    if token != "myprivatekey":
        return JsonResponse({"message": "Authorization token incorrect."}, status=404)
    return None

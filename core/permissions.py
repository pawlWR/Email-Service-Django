from rest_framework import permissions

API_KEY = "fast-a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
API_KEY_NAME = "Email-API-Key"


class HasValidAPIKey(permissions.BasePermission):
    """
    Ensures that the request has a valid API key in the headers.
    """

    def has_permission(self, request, view):
        received_key = request.headers.get(API_KEY_NAME)
        return received_key == API_KEY
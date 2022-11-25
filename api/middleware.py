from django.http import JsonResponse
from rest_framework import  status


class DenyInactiveUser:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if not request.user.is_anonymous and not request.user.is_active:
            return JsonResponse({
                "errors": "User Blocked By Admin",
                "status": status.HTTP_403_FORBIDDEN,
            },
            status=status.HTTP_403_FORBIDDEN,
        )
        response = self.get_response(request)
        return response
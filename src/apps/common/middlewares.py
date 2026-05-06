from django.http import HttpRequest
from typing import Optional


class ClientIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.client_ip = self.get_client_ip(request)
        return self.get_response(request)

    def get_client_ip(self, request: HttpRequest) -> str:
        """Return the client's IP address."""
        forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

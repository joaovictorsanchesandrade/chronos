from django.http import JsonResponse, HttpRequest
from django.utils.translation import gettext as _
from typing import Optional, cast
from apps.common.types import ApplicationRequest, ClientLocation


class ApplicationRequestMiddleware:
    """Request instance for a custom request for my application."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request = cast(ApplicationRequest, request)
        return self.get_response(request)


class ClientIPMiddleware:
    """Get the user's IP address."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: ApplicationRequest):
        request.client_ip = self.get_client_ip(request)
        return self.get_response(request)

    def get_client_ip(self, request: ApplicationRequest) -> str:
        """Return the client's IP address."""
        forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class ClientLocationMiddleware:
    """Retrieves the client location provided in the header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: ApplicationRequest):
        location: Optional[str] = request.headers.get("X-Client-Location")
        if location:
            try:
                lat, lng, accuracy = location.split(",")
                lat, lng, accuracy = (
                    float(lat),
                    float(lng),
                    int(accuracy) if accuracy else None,
                )

                request.client_location = ClientLocation(
                    lat=lat, lng=lng, accuracy=accuracy
                )
            except:
                return JsonResponse(
                    {
                        "detail": _(
                            "Não foi possível interpretar a localização informada. Envie a localização no formato correto: latitude,longitude,precisão."
                        )
                    },
                    status=400,
                )

        return self.get_response(request)

from django.http import HttpRequest
from typing import TypedDict, Optional
from dataclasses import dataclass
from apps.common.models import Employee


@dataclass
class ClientLocation:
    lat: float
    lng: float
    accuracy: int | None = None
    distance: float = 0


class ApplicationRequest(HttpRequest):
    """A customized request from our application."""

    client_ip: Optional[str] = None
    client_location: Optional[ClientLocation] = None
    employee: Optional[Employee] = None

    def __init__(self, request: HttpRequest):
        super().__init__()
        self.__dict__.update(request.__dict__)

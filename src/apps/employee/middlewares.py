from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from apps.common.models import Employee, Business
from apps.common.types import ApplicationRequest, ClientLocation
from apps.common.validators import validate_location
from typing import Optional
import base64


class EmployeeAuthenticateMiddleware:
    """Authenticate or employee using the provided base64 token"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: ApplicationRequest):
        employee_token = request.headers.get("employee-token")
        request.employee = None
        if employee_token:
            json_response = self.authenticate(request, employee_token)
            if json_response:
                return json_response
        return self.get_response(request)

    def authenticate(
        self, request: ApplicationRequest, employee_token: str
    ) -> Optional[JsonResponse]:
        """Authenticates the employee using the provided base64 token."""
        try:
            business_uuid, register, pin = (
                base64.b64decode(employee_token).decode().split(",")
            )
        except Exception as e:
            return JsonResponse(
                {"detail": _("O token de funcionário fornecido é inválido.")},
                status=400,
            )

        business = self.get_business(business_uuid)
        queryset = Employee.objects.filter_by_register(business, register)
        employee: Optional[Employee] = queryset.first()
        if not employee or pin != employee.pin:
            return JsonResponse(
                {"detail": _("Número de registro ou PIN inválido.")}, status=401
            )

        request.employee = employee

    def get_business(self, business_uuid: str) -> Business:
        """Search for the company using the public identifier."""
        queryset = Business.objects.for_employee(business_uuid)
        return get_object_or_404(queryset)


class EmployeeLocationMiddleware:
    """Obtain the employee's location and verify that the location is permitted and meets the company's requirements."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: ApplicationRequest):
        employee: Optional[Employee] = request.employee
        if employee and employee.business.restricted_gps and request.method.upper() != "GET":
            if not request.client_location:
                return JsonResponse(
                    {
                        "detail": _(
                            "Você precisa informar sua localização para que possamos validar sua posição."
                        )
                    },
                    status=400,
                )

            try:
                valid, distance = self.validate_location(
                    request.employee, client_location=request.client_location
                )
                if not valid:
                    return JsonResponse(
                        {"detail": _("Você está fora da área permitida.")}, status=403
                    )
                request.client_location.distance = distance
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

    def validate_location(
        self,
        employee: Employee,
        client_location: ClientLocation,
    ) -> tuple[bool, float | None]:
        """Applying the algorithm to validate the employee's position."""
        valid, distance = validate_location(
            position_check=(
                client_location.lat,
                client_location.lng,
                client_location.accuracy,
            ),
            position_valid=(employee.business.lat, employee.business.lng),
            allowed_radius_meters=employee.business.allowed_radius_meters,
        )
        return valid, distance


class EmployeeNetworkMiddleware:
    """Checks if the employee is on the network specified by the company."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: ApplicationRequest):
        employee: Optional[Employee] = request.employee
        if employee and request.method.upper() != "GET":
            business: Business = employee.business
            ip_allowed = business.ip_is_allowed(request.client_ip)
            if business.restricted_network and not ip_allowed:
                return JsonResponse(
                    {"detail": _("Você não pode acessar através desta rede.")},
                    status=403,
                )
        return self.get_response(request)

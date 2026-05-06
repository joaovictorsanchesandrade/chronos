from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from apps.common.models import Employee, Business
from typing import Optional
import base64


class EmployeeAuthenticateMiddleware:
    """Authenticate or employee using the provided base64 token"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        employee_token = request.headers.get("employee-token")
        request.employee = None
        if employee_token:
            json_response = self.authenticate(request, employee_token)
            if json_response:
                return json_response
        return self.get_response(request)

    def authenticate(
        self, request: HttpRequest, employee_token: str
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

        ip_allowed = business.ip_is_allowed(request.client_ip)
        if not ip_allowed:
            return JsonResponse(
                {"detail": _("Você não pode acessar através desta rede.")},
                status=403,
            )

        request.employee = employee

    def get_business(self, business_uuid: str) -> Business:
        """Search for the company using the public identifier."""
        queryset = Business.objects.for_employee(business_uuid)
        return get_object_or_404(queryset)

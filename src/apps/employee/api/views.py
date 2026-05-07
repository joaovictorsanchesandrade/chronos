from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.request import HttpRequest
from rest_framework.response import Response
from rest_framework import status
from apps.common.models import Business
from apps.common.types import ApplicationRequest
from apps.employee.api.serializers import (
    ClockingSerializer,
    EmployeeSerializer,
    WorkSessionSerializer,
)
from apps.employee.services import create_time_record, get_current_work_session
from apps.employee.api.permissions import IsEmployee


def get_business(public_uuid: str) -> Business:
    """Returns the business information for the employee to use."""
    queryset = Business.objects.for_employee(public_uuid)
    return get_object_or_404(queryset)


class EmployeeView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request: ApplicationRequest):
        return Response(
            EmployeeSerializer(request.employee, context={"request": request}).data
        )


class WorkSessionView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request: ApplicationRequest):
        work_session = get_current_work_session(employee=request.employee)
        if work_session:
            serializer = WorkSessionSerializer(
                work_session, context={"request": request}
            )
            return Response(serializer.data)
        return Response(
            {"detail": _("Não encotramos nenhuma jornada iniciada")}, status=404
        )

    def post(self, request: ApplicationRequest):
        serializer = ClockingSerializer(
            data=request.data, context={"employee": request.employee}
        )
        serializer.is_valid(raise_exception=True)
        create_time_record(
            employee=request.employee,
            record_type=serializer.validated_data["record_type"],
            client_ip=request.client_ip,
            client_location=request.client_location,
        )
        return Response(status=status.HTTP_201_CREATED)

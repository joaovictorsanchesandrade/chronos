from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from apps.common.api.pagination import DefaultPageNumberPagination
from apps.common.models import Employee, Business
from apps.business.api.serializers import EmployeeSerializer, WorkSessionSerializer


class EmployeeListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer
    pagination_class = DefaultPageNumberPagination

    def get_business(self):
        business_uuid = self.kwargs["business_uuid"]
        return get_object_or_404(
            Business.objects.filter_by_public_uuid(self.request.user, business_uuid)
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["business"] = self.get_business()
        return context

    def get_queryset(self):
        business = self.get_business()
        return Employee.objects.filter_by_business(business)


class EmployeeRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer
    lookup_url_kwarg = "public_uuid"
    lookup_field = "public_uuid"

    def get_queryset(self):
        business_uuid = self.kwargs["business_uuid"]
        return Employee.objects.filter(
            is_deleted=False,
            business__public_uuid=business_uuid,
            business__owner=self.request.user,
        )

    def perform_destroy(self, instance: Employee):
        instance.user_delete()


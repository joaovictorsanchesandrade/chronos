from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from apps.business.api.serializers import BusinessSerializer
from apps.common.models import Business
from apps.common.api.pagination import DefaultPageNumberPagination


class BusinessListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessSerializer
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return Business.objects.filter_owner(self.request.user)


class BusinessRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessSerializer
    lookup_field = "public_uuid"
    lookup_url_kwarg = "public_uuid"

    def get_queryset(self):
        return Business.objects.filter_owner(self.request.user)

    def perform_destroy(self, instance: Business):
        instance.user_delete()

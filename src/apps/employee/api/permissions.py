from rest_framework.permissions import BasePermission


class IsEmployee(BasePermission):
    """You must be authenticated as an employee."""

    def has_permission(self, request, view):
        return request.employee is not None

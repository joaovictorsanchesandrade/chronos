from django.urls import path
from apps.business.api import views

app_name = "api-business"
urlpatterns = [
    path(
        "", views.business.BusinessListCreateView.as_view(), name="business-list-create"
    ),
    path(
        "<str:public_uuid>/",
        views.business.BusinessRetrieveUpdateDestroyView.as_view(),
        name="business-retrieve-update-destroy",
    ),
    path(
        "<str:business_uuid>/employees/",
        views.employee.EmployeeListCreateView.as_view(),
        name="employee-list-create",
    ),
    path(
        "<str:business_uuid>/employees/<str:public_uuid>/",
        views.employee.EmployeeRetrieveUpdateDestroyView.as_view(),
        name="employee-retrieve-update-destroy",
    ),
]

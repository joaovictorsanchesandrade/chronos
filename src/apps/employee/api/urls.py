from django.urls import path
from apps.employee.api import views

app_name = "api-employee"
urlpatterns = [
    path("", views.EmployeeView.as_view(), name="profile"),
    path("worksessions/", views.WorkSessionView.as_view(), name="work-sessions"),
]

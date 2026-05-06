from django.urls import path
from apps.employee.pages import views

app_name = "page-employee"
urlpatterns = [path("clocking/<str:public_uuid>/", views.clocking_page, name="clocking")]

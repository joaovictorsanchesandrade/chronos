from django.urls import path
from apps.business.pages.views import DashboardView

app_name = "page-business"
urlpatterns = [path("dashboard/", DashboardView.as_view(), name="dashboard")]

from django.urls import path
from config.health import LiveView, ReadyView

urlpatterns = [
    path("health/live", LiveView.as_view(), name="health-live"),
    path("health/ready", ReadyView.as_view(), name="health-ready"),
    path("api/v1/health/live", LiveView.as_view(), name="api-health-live"),
    path("api/v1/health/ready", ReadyView.as_view(), name="api-health-ready"),
]

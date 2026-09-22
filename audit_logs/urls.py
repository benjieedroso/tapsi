from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "audit_logs"
router = DefaultRouter()
router.register(r"records", views.AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("", views.audit_log_list, name="audit_log_list"),
]

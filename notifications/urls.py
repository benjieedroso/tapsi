from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "notifications"

router = DefaultRouter()
router.register(r"records", views.NotificationViewSet, basename="notification")

urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("api/v1/", include(router.urls)),
    path("<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),
    path("read-all/", views.notification_mark_all_read, name="notification_mark_all_read"),
]

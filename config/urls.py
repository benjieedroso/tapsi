from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from accounts import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("menu/", include("menu.urls")),
    path("inventory/", include("inventory.urls")),
    path("suppliers/", include("suppliers.urls")),
    path("recipes/", include("recipes.urls")),
    path("orders/", include("orders.urls")),
    path("expenses/", include("expenses.urls")),
    path("employees/", include("employees.urls")),
    path("closing/", include("closing.urls")),
    path("notifications/", include("notifications.urls")),
    path("audit-logs/", include("audit_logs.urls")),
    path("reports/", include("reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

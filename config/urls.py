from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from accounts.views import CurrentUserView
from django.views.generic import RedirectView


urlpatterns = [
    # 2. Redirect empty root path to /admin/
    path("", RedirectView.as_view(url="/admin/", permanent=False)),

    # Admin Interface
    path("admin/", admin.site.urls),

    # Decoupled REST API Endpoints (v1)
    # Authentication & User Profile
    path("api/v1/", include("accounts.urls")),

    # Domain Modules
    path("api/v1/menu/", include("menu.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/inventory/", include("inventory.urls")),
    path("api/v1/expenses/", include("expenses.urls")),
    path("api/v1/employees/", include("employees.urls")),
    path("api/v1/suppliers/", include("suppliers.urls")),
    path("api/v1/closing/", include("closing.urls")),
    path("api/v1/reports/", include("reports.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/audit-logs/", include("audit_logs.urls")),

    # Legacy HTML / Monolith Routes (Commented out for SPA decoupling)
    # path("", views.dashboard, name="dashboard"),
    # path("accounts/", include("accounts.urls")),
    # path("menu/", include("menu.urls")),
    # path("inventory/", include("inventory.urls")),
    # path("suppliers/", include("suppliers.urls")),
    # path("recipes/", include("recipes.urls")),
    # path("orders/", include("orders.urls")),
    # path("expenses/", include("expenses.urls")),
    # path("employees/", include("employees.urls")),
    # path("closing/", include("closing.urls")),
    # path("notifications/", include("notifications.urls")),
    # path("audit-logs/", include("audit_logs.urls")),
    # path("reports/", include("reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
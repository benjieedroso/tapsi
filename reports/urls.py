from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "reports"
router = DefaultRouter()
# Register under 'analytics' or 'records'
router.register(r"analytics", views.ReportViewSet, basename="report")

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("", views.daily_sales, name="daily_sales"),
    path("daily-sales/", views.daily_sales, name="daily_sales"),
    path("monthly-sales/", views.monthly_sales, name="monthly_sales"),
    path("profit-loss/", views.profit_loss, name="profit_loss"),
    path("inventory/", views.inventory_report, name="inventory_report"),
    path("product-mix/", views.product_mix, name="product_mix"),
    path("purchases/", views.purchase_report, name="purchase_report"),
    path("tax-summary/", views.tax_summary, name="tax_summary"),
]

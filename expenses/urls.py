from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"records", views.ExpenseViewSet, basename="expense")
app_name = "expenses"

urlpatterns = [
    #DRF API routes
    path("api/v1/", include(router.urls)),
    #Legacy routes
    path("", views.expense_list, name="expense_list"),
    path("new/", views.expense_create, name="expense_create"),
    path("<int:pk>/edit/", views.expense_edit, name="expense_edit"),
    path("<int:pk>/delete/", views.expense_delete, name="expense_delete"),
    path("<int:pk>/approve/", views.expense_approve, name="expense_approve"),
]

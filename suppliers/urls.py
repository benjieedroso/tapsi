from django.urls import path

from . import views

app_name = "suppliers"

urlpatterns = [
    # Suppliers (FR-050..FR-053)
    path("", views.supplier_list, name="supplier_list"),
    path("new/", views.supplier_create, name="supplier_create"),
    path("<int:pk>/", views.supplier_detail, name="supplier_detail"),
    path("<int:pk>/edit/", views.supplier_edit, name="supplier_edit"),
    path("<int:pk>/delete/", views.supplier_delete, name="supplier_delete"),
    path("<int:pk>/payments/", views.supplier_payment_create, name="supplier_payment_create"),
    # Purchase orders (FR-060..FR-065)
    path("purchase-orders/", views.po_list, name="po_list"),
    path("purchase-orders/new/", views.po_create, name="po_create"),
    path("purchase-orders/<int:pk>/", views.po_detail, name="po_detail"),
    path("purchase-orders/<int:pk>/edit/", views.po_edit, name="po_edit"),
    path("purchase-orders/<int:pk>/place/", views.po_place, name="po_place"),
    path("purchase-orders/<int:pk>/cancel/", views.po_cancel, name="po_cancel"),
    path("purchase-orders/<int:pk>/receive/", views.po_receive, name="po_receive"),
]

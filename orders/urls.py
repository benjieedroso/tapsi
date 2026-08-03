from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    # Tables (FR-090..FR-095)
    path("tables/", views.table_list, name="table_list"),
    path("tables/new/", views.table_create, name="table_create"),
    path("tables/<int:pk>/edit/", views.table_edit, name="table_edit"),
    path("tables/<int:pk>/delete/", views.table_delete, name="table_delete"),
    path("tables/<int:pk>/status/", views.table_status, name="table_status"),
    # Orders (FR-080..FR-089)
    path("", views.order_list, name="order_list"),
    path("new/", views.order_create, name="order_create"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
    path("<int:pk>/items/add/", views.order_item_add, name="order_item_add"),
    path("<int:pk>/items/<int:item_pk>/edit/", views.order_item_edit, name="order_item_edit"),
    path("<int:pk>/items/<int:item_pk>/remove/", views.order_item_remove, name="order_item_remove"),
    path("<int:pk>/discount/", views.order_discount, name="order_discount"),
    path("<int:pk>/discount/approve/", views.order_discount_approve, name="order_discount_approve"),
    path("<int:pk>/cancel/", views.order_cancel, name="order_cancel"),
    path("<int:pk>/complete/", views.order_complete, name="order_complete"),
    path("<int:pk>/transfer/", views.order_transfer, name="order_transfer"),
    path("<int:pk>/merge/", views.order_merge, name="order_merge"),
    # Kitchen (FR-088, FR-089)
    path("kitchen/queue/", views.kitchen_queue, name="kitchen_queue"),
    path("kitchen/<int:pk>/advance/", views.kitchen_advance, name="kitchen_advance"),
    # Payments & receipts (FR-100..FR-106)
    path("<int:pk>/payments/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/refund/", views.payment_refund, name="payment_refund"),
    path("<int:pk>/receipt/", views.receipt, name="receipt"),
    path("<int:pk>/receipt/reprint/", views.receipt, {"reprint": True}, name="receipt_reprint"),
]

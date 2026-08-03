from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem, Supplier, SupplierPayment


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "payment_terms", "is_active", "is_deleted")
    list_filter = ("payment_terms", "is_active", "is_deleted")
    search_fields = ("name", "contact_person")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "status", "expected_date", "created_at")
    list_filter = ("status",)
    search_fields = ("po_number", "supplier__name")
    inlines = [PurchaseOrderItemInline]
    readonly_fields = ("po_number",)


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ("supplier", "amount", "payment_date", "method", "recorded_by")
    list_filter = ("method",)
    date_hierarchy = "payment_date"

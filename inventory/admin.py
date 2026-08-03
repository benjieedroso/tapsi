from django.contrib import admin

from .models import Ingredient, InventoryTransaction, LowStockAlert


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "unit_of_measure", "minimum_stock", "average_unit_cost", "is_deleted")
    list_filter = ("unit_of_measure", "is_deleted")
    search_fields = ("name",)


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    """Ledger is append-only: no add, no delete (FR-043)."""
    list_display = ("ingredient", "transaction_type", "quantity", "resulting_balance", "reference", "user", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("ingredient__name", "reference", "reason")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "restaurant_id", "opened_at", "resolved_at")
    list_filter = ("resolved_at",)

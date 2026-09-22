from rest_framework import serializers
from .models import Ingredient, InventoryTransaction, LowStockAlert

class IngredientSerializer(serializers.ModelSerializer):
    # Expose derived property fields explicitly
    current_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "unit_of_measure",
            "minimum_stock",
            "average_unit_cost",
            "default_supplier_id",
            "current_stock",
            "is_low_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "average_unit_cost",
            "created_at",
            "updated_at",
        ]


class InventoryTransactionSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.ReadOnlyField(source="ingredient.name")
    user_username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = InventoryTransaction
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "transaction_type",
            "quantity",
            "unit_cost",
            "resulting_balance",
            "reference",
            "reason",
            "user",
            "user_username",
            "created_at",
        ]
        # Fields set automatically by model save() logic
        read_only_fields = ["resulting_balance", "user", "created_at"]


class LowStockAlertSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.ReadOnlyField(source="ingredient.name")

    class Meta:
        model = LowStockAlert
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "opened_at",
            "resolved_at",
        ]
        read_only_fields = fields
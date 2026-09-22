from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source="created_by.username")
    approved_by_username = serializers.ReadOnlyField(source="approved_by.username")

    class Meta:
        model = Expense
        fields = [
            "id",
            "category",
            "amount",
            "expense_date",
            "payee",
            "payment_method",
            "notes",
            "receipt_image",
            "status",
            "created_by",
            "created_by_username",
            "approved_by",
            "approved_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
        ]
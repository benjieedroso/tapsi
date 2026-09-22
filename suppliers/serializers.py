from rest_framework import serializers
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPayment


class SupplierSerializer(serializers.ModelSerializer):
    has_purchase_orders = serializers.ReadOnlyField()
    outstanding_balance = serializers.ReadOnlyField()

    class Meta:
        model = Supplier
        fields = [
            "id",
            "restaurant_id",
            "name",
            "contact_person",
            "phone",
            "email",
            "address",
            "payment_terms",
            "is_active",
            "is_deleted",
            "deleted_at",
            "has_purchase_orders",
            "outstanding_balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "restaurant_id",
            "is_deleted",
            "deleted_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        restaurant_id = getattr(request.user, "restaurant_id", None)
        return Supplier.objects.create(restaurant_id=restaurant_id, **validated_data)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.ReadOnlyField(source="ingredient.name")
    unit_of_measure = serializers.ReadOnlyField(source="ingredient.unit_of_measure")
    outstanding_qty = serializers.ReadOnlyField()
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "unit_of_measure",
            "qty_ordered",
            "qty_received",
            "unit_cost",
            "outstanding_qty",
            "line_total",
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, required=False)
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    placed_by_name = serializers.ReadOnlyField(source="placed_by.get_full_name")
    total = serializers.ReadOnlyField()
    received_total = serializers.ReadOnlyField()
    is_read_only = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "restaurant_id",
            "po_number",
            "supplier",
            "supplier_name",
            "status",
            "expected_date",
            "notes",
            "placed_by",
            "placed_by_name",
            "total",
            "received_total",
            "is_read_only",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "restaurant_id",
            "po_number",
            "status",
            "placed_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        restaurant_id = getattr(request.user, "restaurant_id", None)
        user = request.user if request and request.user.is_authenticated else None

        po = PurchaseOrder.objects.create(
            restaurant_id=restaurant_id,
            placed_by=user,
            **validated_data
        )

        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=po, **item_data)

        return po

    def update(self, instance, validated_data):
        if instance.is_read_only:
            raise serializers.ValidationError("Received purchase orders cannot be modified.")

        items_data = validated_data.pop("items", None)

        instance.supplier = validated_data.get("supplier", instance.supplier)
        instance.expected_date = validated_data.get("expected_date", instance.expected_date)
        instance.notes = validated_data.get("notes", instance.notes)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                PurchaseOrderItem.objects.create(purchase_order=instance, **item_data)

        return instance


class SupplierPaymentSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    recorded_by_name = serializers.ReadOnlyField(source="recorded_by.get_full_name")

    class Meta:
        model = SupplierPayment
        fields = [
            "id",
            "restaurant_id",
            "supplier",
            "supplier_name",
            "amount",
            "payment_date",
            "method",
            "reference_no",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "created_at",
        ]
        read_only_fields = ["restaurant_id", "recorded_by", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        restaurant_id = getattr(request.user, "restaurant_id", None)
        user = request.user if request and request.user.is_authenticated else None

        return SupplierPayment.objects.create(
            restaurant_id=restaurant_id,
            recorded_by=user,
            **validated_data
        )
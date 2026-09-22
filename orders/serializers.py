from rest_framework import serializers
from .models import Order, OrderItem, OrderItemAddon, generate_order_number


class OrderItemAddonSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemAddon
        fields = ["id", "addon", "addon_name", "price"]
        read_only_fields = ["addon_name", "price"]


class OrderItemSerializer(serializers.ModelSerializer):
    addons = OrderItemAddonSerializer(many=True, required=False)
    menu_item_name = serializers.ReadOnlyField(source="item_name")

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "item_name",
            "menu_item_name",
            "unit_price",
            "quantity",
            "notes",
            "addons",
            "line_total",
        ]
        read_only_fields = ["item_name", "line_total"]

    def validate(self, attrs):
        menu_item = attrs.get("menu_item")
        if not menu_item:
            raise serializers.ValidationError({"menu_item": "Menu item is required."})

        # Snapshot item_name and unit_price if not provided
        if "item_name" not in attrs or not attrs["item_name"]:
            attrs["item_name"] = menu_item.name
        if "unit_price" not in attrs or attrs["unit_price"] is None:
            attrs["unit_price"] = menu_item.price

        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "restaurant_id",
            "order_number",
            "reference",
            "order_type",
            "table",
            "status",
            "business_date",
            "subtotal",
            "discount_type",
            "discount_ref",
            "discount_amount",
            "manual_discount_pct",
            "discount_needs_approval",
            "vatable_sales",
            "vat_exempt_sales",
            "vat_amount",
            "total",
            "customer_name",
            "customer_phone",
            "customer_address",
            "created_by",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "restaurant_id",
            "order_number",
            "reference",
            "business_date",
            "subtotal",
            "discount_amount",
            "discount_needs_approval",
            "vatable_sales",
            "vat_exempt_sales",
            "vat_amount",
            "total",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        
        # Retrieve restaurant_id from view helper or user context
        restaurant_id = getattr(request.user, "restaurant_id", None)
        if not restaurant_id and hasattr(request.user, "restaurant"):
            restaurant_id = request.user.restaurant.id

        user = request.user if request and request.user.is_authenticated else None

        # FR-081: Generate per-restaurant, per-day order number
        order = Order.objects.create(
            restaurant_id=restaurant_id,
            created_by=user,
            **validated_data,
        )
        order.order_number = generate_order_number(restaurant_id, order.business_date)
        order.save(update_fields=["order_number"])

        # Create OrderItems and snapshot details
        for item_data in items_data:
            addons_data = item_data.pop("addons", [])
            menu_item = item_data.get("menu_item")

            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=item_data.get("item_name", menu_item.name if menu_item else ""),
                unit_price=item_data.get("unit_price", menu_item.price if menu_item else 0),
                quantity=item_data.get("quantity", 1),
                notes=item_data.get("notes", ""),
            )

            # Snapshot Addons
            for addon_data in addons_data:
                addon = addon_data.get("addon")
                OrderItemAddon.objects.create(
                    order_item=order_item,
                    addon=addon,
                    addon_name=addon.name if addon else addon_data.get("addon_name", ""),
                    price=addon.price if addon else addon_data.get("price", 0),
                )

        # BR-011 / FR-087: Recompute subtotal, VAT, and discounts
        order.recompute_totals(user=user)
        return order
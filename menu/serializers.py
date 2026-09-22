from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, MenuItem, MenuItemPriceHistory, AddOn, MenuItemAddOn

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """FR-030: Category Serializer."""

    class Meta:
        model = Category
        fields = [
            "id",
            "restaurant_id",
            "name",
            "display_order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "restaurant_id", "created_at"]


class AddOnSerializer(serializers.ModelSerializer):
    """FR-033: AddOn Serializer."""

    class Meta:
        model = AddOn
        fields = ["id", "restaurant_id", "name", "price", "is_available", "created_at"]
        read_only_fields = ["id", "restaurant_id", "created_at"]


class UserSimpleSerializer(serializers.ModelSerializer):
    """Nested user representation for price history log."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class MenuItemPriceHistorySerializer(serializers.ModelSerializer):
    """FR-036: Price History Serializer."""

    changed_by = UserSimpleSerializer(read_only=True)

    class Meta:
        model = MenuItemPriceHistory
        fields = ["id", "menu_item", "old_price", "new_price", "changed_by", "created_at"]
        read_only_fields = fields


class MenuItemSerializer(serializers.ModelSerializer):
    """FR-031, FR-034, FR-035: Menu Item Serializer."""

    category_details = CategorySerializer(source="category", read_only=True)
    addons = AddOnSerializer(many=True, read_only=True)
    addon_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "restaurant_id",
            "category",
            "category_details",
            "name",
            "description",
            "price",
            "prep_minutes",
            "is_available",
            "image",
            "addons",
            "addon_ids",
            "is_deleted",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "restaurant_id",
            "is_deleted",
            "deleted_at",
            "created_at",
            "updated_at",
        ]

    def validate_category(self, value):
        """Ensure category belongs to the current user's restaurant."""
        if value:
            request = self.context.get("request")
            if request and value.restaurant_id != request.user.restaurant_id:
                raise serializers.ValidationError(
                    "Selected category does not belong to your restaurant."
                )
        return value

    def to_representation(self, instance):
        """Include attached AddOns in GET responses."""
        representation = super().to_representation(instance)
        attached_addons = AddOn.objects.filter(
            menu_item_links__menu_item=instance
        )
        representation["addons"] = AddOnSerializer(attached_addons, many=True).data
        return representation

    def create(self, validated_data):
        addon_ids = validated_data.pop("addon_ids", [])
        menu_item = MenuItem.objects.create(**validated_data)

        if addon_ids:
            restaurant_id = menu_item.restaurant_id
            valid_addons = AddOn.objects.filter(id__in=addon_ids, restaurant_id=restaurant_id)
            links = [MenuItemAddOn(menu_item=menu_item, addon=addon) for addon in valid_addons]
            MenuItemAddOn.objects.bulk_create(links)

        return menu_item

    def update(self, instance, validated_data):
        addon_ids = validated_data.pop("addon_ids", None)
        instance = super().update(instance, validated_data)

        if addon_ids is not None:
            MenuItemAddOn.objects.filter(menu_item=instance).delete()
            valid_addons = AddOn.objects.filter(
                id__in=addon_ids, restaurant_id=instance.restaurant_id
            )
            links = [MenuItemAddOn(menu_item=instance, addon=addon) for addon in valid_addons]
            MenuItemAddOn.objects.bulk_create(links)

        return instance
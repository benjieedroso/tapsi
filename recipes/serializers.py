from rest_framework import serializers
from .models import Recipe, RecipeIngredient
from menu.models import MenuItem, AddOn


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.ReadOnlyField(source="ingredient.name")
    unit_of_measure = serializers.ReadOnlyField(source="ingredient.unit_of_measure")
    line_cost = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "unit_of_measure",
            "quantity",
            "line_cost",
        ]


class RecipeSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), source="menu_item", write_only=True, required=False, allow_null=True
    )
    addon_id = serializers.PrimaryKeyRelatedField(
        queryset=AddOn.objects.all(), source="addon", write_only=True, required=False, allow_null=True
    )
    
    menu_item = serializers.StringRelatedField(read_only=True)
    addon = serializers.StringRelatedField(read_only=True)
    lines = RecipeIngredientSerializer(many=True, read_only=True)

    ingredient_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, write_only=True, required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "menu_item",
            "menu_item_id",
            "addon",
            "addon_id",
            "ingredient_id",
            "quantity",
            "cost",
            "margin",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["cost", "margin", "lines"]

    def create(self, validated_data):
        ingredient_id = validated_data.pop("ingredient_id", None)
        quantity = validated_data.pop("quantity", None)
        
        # Guaranteed restaurant_id resolution
        view = self.context.get("view")
        request = self.context.get("request")

        if "restaurant_id" not in validated_data:
            if view and hasattr(view, "get_restaurant_id"):
                validated_data["restaurant_id"] = view.get_restaurant_id()
            elif request and hasattr(request, "user") and hasattr(request.user, "restaurant_id"):
                validated_data["restaurant_id"] = request.user.restaurant_id
            else:
                validated_data["restaurant_id"] = int(request.headers.get("X-Restaurant-ID", 1))

        recipe = Recipe.objects.create(**validated_data)

        if ingredient_id and quantity:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                quantity=quantity
            )

        return recipe
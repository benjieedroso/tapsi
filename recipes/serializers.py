from rest_framework import serializers
from .models import Recipe, RecipeIngredient


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
    lines = RecipeIngredientSerializer(many=True, required=False)
    menu_item_name = serializers.ReadOnlyField(source="menu_item.name")
    addon_name = serializers.ReadOnlyField(source="addon.name")
    cost = serializers.ReadOnlyField()
    margin = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "addon",
            "addon_name",
            "name",
            "cost",
            "margin",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        menu_item = attrs.get("menu_item")
        addon = attrs.get("addon")

        if not menu_item and not addon:
            raise serializers.ValidationError("A recipe must be linked to either a MenuItem or an AddOn.")
        if menu_item and addon:
            raise serializers.ValidationError("A recipe cannot be linked to both a MenuItem and an AddOn simultaneously.")

        return attrs

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        request = self.context.get("request")
        restaurant_id = getattr(request.user, "restaurant_id", None)

        recipe = Recipe.objects.create(restaurant_id=restaurant_id, **validated_data)

        for line_data in lines_data:
            RecipeIngredient.objects.create(recipe=recipe, **line_data)

        return recipe

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)

        instance.menu_item = validated_data.get("menu_item", instance.menu_item)
        instance.addon = validated_data.get("addon", instance.addon)
        instance.name = validated_data.get("name", instance.name)
        instance.save()

        if lines_data is not None:
            # Replace lines on update
            instance.lines.all().delete()
            for line_data in lines_data:
                RecipeIngredient.objects.create(recipe=instance, **line_data)

        return instance
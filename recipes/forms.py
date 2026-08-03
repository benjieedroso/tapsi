from django import forms
from django.core.exceptions import ValidationError

from inventory.models import Ingredient
from menu.models import AddOn, MenuItem

from .models import Recipe, RecipeIngredient


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class RecipeForm(StyledFormMixin, forms.ModelForm):
    """FR-070: attach a recipe to one menu item OR one add-on."""
    menu_item = forms.ModelChoiceField(
        queryset=MenuItem.objects.none(),
        required=False,
        label="Menu Item",
    )
    addon = forms.ModelChoiceField(
        queryset=AddOn.objects.none(),
        required=False,
        label="Add-On",
    )
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.none(),
        required=False,
        label="Ingredient (first line)",
    )
    quantity = forms.DecimalField(
        max_digits=12, decimal_places=3, min_value=0.001,
        required=False, label="Quantity",
    )

    class Meta:
        model = Recipe
        fields = ("name",)

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["menu_item"].queryset = MenuItem.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False
        ).order_by("name")
        self.fields["addon"].queryset = AddOn.objects.filter(
            restaurant_id=restaurant_id
        ).order_by("name")
        self.fields["ingredient"].queryset = Ingredient.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False
        ).order_by("name")
        self._apply_classes()

    def clean(self):
        cleaned = super().clean()
        menu_item = cleaned.get("menu_item")
        addon = cleaned.get("addon")
        if bool(menu_item) == bool(addon):
            raise ValidationError("Choose exactly one target: a menu item OR an add-on.")
        ingredient = cleaned.get("ingredient")
        if ingredient is not None:
            if cleaned.get("quantity") is None:
                self.add_error("quantity", "Quantity is required for the ingredient line.")
            if (
                self.instance.pk
                and RecipeIngredient.objects.filter(
                    recipe=self.instance, ingredient=ingredient
                ).exists()
            ):
                self.add_error(
                    "ingredient",
                    f"\"{ingredient.name}\" is already in this recipe.",
                )
        return cleaned


class RecipeIngredientForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ("ingredient", "quantity")
        widgets = {
            "quantity": forms.NumberInput(attrs={"step": "0.001", "min": "0.001"}),
        }

    def __init__(self, *args, restaurant_id=None, recipe=None, **kwargs):
        self.restaurant_id = restaurant_id
        self.recipe = recipe
        super().__init__(*args, **kwargs)
        self.fields["ingredient"].queryset = Ingredient.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False
        ).order_by("name")
        self._apply_classes()

    def clean_ingredient(self):
        ingredient = self.cleaned_data.get("ingredient")
        if (
            ingredient is not None
            and self.recipe is not None
            and RecipeIngredient.objects.filter(
                recipe=self.recipe, ingredient=ingredient
            ).exists()
        ):
            raise ValidationError(
                f"\"{ingredient.name}\" is already in this recipe."
            )
        return ingredient

    def clean_quantity(self):
        value = self.cleaned_data.get("quantity")
        if value is None or value <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return value

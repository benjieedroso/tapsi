from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from menu.models import MenuItem, AddOn
from inventory.models import Ingredient

from menu.views import TenantAwareViewSet
from inventory.models import Ingredient

from accounts.models import User

from .forms import RecipeForm, RecipeIngredientForm
from .models import Recipe, RecipeIngredient
from .serializers import RecipeSerializer

def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _is_staff_or_manager(user):
    """Kitchen has read access to recipes (SRS matrix); Cashier does not."""
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER, User.Role.KITCHEN}


def _restaurant_id(user):
    return user.restaurant_id


# ── Recipe Views (FR-070, FR-071, FR-075) ───────────────────────────


@user_passes_test(_is_staff_or_manager)
def recipe_list(request):
    rid = _restaurant_id(request.user)
    recipes = Recipe.objects.filter(restaurant_id=rid).prefetch_related(
        "lines__ingredient", "menu_item", "addon"
    )
    return render(request, "recipes/recipe_list.html", {"recipes": recipes})


@user_passes_test(_is_manager_or_above)
def recipe_create(request):
    rid = _restaurant_id(request.user)
    form = RecipeForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        recipe = form.save(commit=False)
        recipe.restaurant_id = rid
        recipe.menu_item = form.cleaned_data.get("menu_item")
        recipe.addon = form.cleaned_data.get("addon")
        if not recipe.name:
            recipe.name = (
                recipe.menu_item.name if recipe.menu_item
                else recipe.addon.name if recipe.addon else "Recipe"
            )
        recipe.save()
        ingredient = form.cleaned_data.get("ingredient")
        if ingredient is not None:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=form.cleaned_data["quantity"],
            )
        messages.success(request, f"Recipe for \"{recipe.target}\" created.")
        return redirect("recipes:recipe_detail", pk=recipe.pk)
    return render(request, "recipes/recipe_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def recipe_detail(request, pk):
    rid = _restaurant_id(request.user)
    recipe = get_object_or_404(Recipe, pk=pk, restaurant_id=rid)
    line_form = RecipeIngredientForm(restaurant_id=rid)
    return render(request, "recipes/recipe_detail.html", {
        "recipe": recipe,
        "line_form": line_form,
    })


@user_passes_test(_is_manager_or_above)
def recipe_edit(request, pk):
    rid = _restaurant_id(request.user)
    recipe = get_object_or_404(Recipe, pk=pk, restaurant_id=rid)
    form = RecipeForm(request.POST or None, instance=recipe, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        recipe = form.save(commit=False)
        recipe.menu_item = form.cleaned_data.get("menu_item")
        recipe.addon = form.cleaned_data.get("addon")
        recipe.save()
        ingredient = form.cleaned_data.get("ingredient")
        if ingredient is not None:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=form.cleaned_data["quantity"],
            )
        messages.success(request, f"Recipe \"{recipe.name}\" updated.")
        return redirect("recipes:recipe_detail", pk=recipe.pk)
    return render(request, "recipes/recipe_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def recipe_delete(request, pk):
    rid = _restaurant_id(request.user)
    recipe = get_object_or_404(Recipe, pk=pk, restaurant_id=rid)
    recipe.delete()
    messages.success(request, f"Recipe \"{recipe.name}\" deleted.")
    return redirect("recipes:recipe_list")


@user_passes_test(_is_manager_or_above)
def recipe_line_add(request, pk):
    rid = _restaurant_id(request.user)
    recipe = get_object_or_404(Recipe, pk=pk, restaurant_id=rid)
    form = RecipeIngredientForm(request.POST or None, restaurant_id=rid, recipe=recipe)
    if form.is_valid():
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=form.cleaned_data["ingredient"],
            quantity=form.cleaned_data["quantity"],
        )
        messages.success(request, "Ingredient line added.")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("recipes:recipe_detail", pk=recipe.pk)


@user_passes_test(_is_manager_or_above)
@require_POST
def recipe_line_remove(request, pk, line_pk):
    rid = _restaurant_id(request.user)
    recipe = get_object_or_404(Recipe, pk=pk, restaurant_id=rid)
    line = get_object_or_404(RecipeIngredient, pk=line_pk, recipe=recipe)
    line.delete()
    messages.success(request, "Ingredient line removed.")
    return redirect("recipes:recipe_detail", pk=recipe.pk)

#New Code
class TenantAwareViewSet(viewsets.ModelViewSet):
    def get_restaurant_id(self):
        if hasattr(self.request.user, "restaurant_id") and self.request.user.restaurant_id:
            return self.request.user.restaurant_id
        return int(self.request.headers.get("X-Restaurant-ID", 1))

    def perform_create(self, serializer):
        serializer.save(restaurant_id=self.get_restaurant_id())


class RecipeViewSet(TenantAwareViewSet):
    serializer_class = RecipeSerializer

    def get_queryset(self):
        rid = self.get_restaurant_id()
        queryset = Recipe.objects.filter(restaurant_id=rid).prefetch_related(
            "lines__ingredient", "menu_item", "addon"
        )

        menu_item_id = self.request.query_params.get("menu_item")
        addon_id = self.request.query_params.get("addon")

        if menu_item_id:
            queryset = queryset.filter(menu_item_id=menu_item_id)
        if addon_id:
            queryset = queryset.filter(addon_id=addon_id)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Custom retrieve to include ingredient meta for the detail view form."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        rid = self.get_restaurant_id()
        ingredients = Ingredient.objects.filter(restaurant_id=rid)
        
        return Response({
            "recipe": serializer.data,
            "meta": {
                "ingredients": [
                    {"id": i.id, "name": i.name, "unit_of_measure": getattr(i, "unit_of_measure", "")} 
                    for i in ingredients
                ]
            }
        })

    @action(detail=False, methods=["get"], url_path="meta")
    def meta(self, request):
        rid = self.get_restaurant_id()
        menu_items = MenuItem.objects.filter(restaurant_id=rid)
        addons = AddOn.objects.filter(restaurant_id=rid)
        ingredients = Ingredient.objects.filter(restaurant_id=rid)

        return Response({
            "menu_items": [{"id": m.id, "name": m.name} for m in menu_items],
            "addons": [{"id": a.id, "name": a.name} for a in addons],
            "ingredients": [
                {"id": i.id, "name": i.name, "unit_of_measure": getattr(i, "unit_of_measure", "")} 
                for i in ingredients
            ],
        })

    @action(detail=False, methods=["get"], url_path="by-target")
    def get_by_target(self, request):
        menu_item_id = request.query_params.get("menu_item")
        addon_id = request.query_params.get("addon")

        recipe = Recipe.get_for(menu_item=menu_item_id, addon=addon_id)
        if not recipe or recipe.restaurant_id != self.get_restaurant_id():
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="lines")
    def add_line(self, request, pk=None):
        """Adds an ingredient line to an existing recipe."""
        recipe = self.get_object()
        
        ingredient_id = request.data.get("ingredient_id")
        quantity = request.data.get("quantity")

        if not ingredient_id or not quantity:
            return Response(
                {"detail": "Both ingredient_id and quantity are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if line already exists for this ingredient, update or create
        line, created = RecipeIngredient.objects.update_or_create(
            recipe=recipe,
            ingredient_id=ingredient_id,
            defaults={"quantity": quantity}
        )

        serializer = RecipeSerializer(recipe, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


    @action(detail=True, methods=["delete"], url_path="lines/(?P<line_id>[^/.]+)")
    def remove_line(self, request, pk=None, line_id=None):
        """Removes an ingredient line from a recipe."""
        recipe = self.get_object()
        try:
            line = RecipeIngredient.objects.get(id=line_id, recipe=recipe)
            line.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RecipeIngredient.DoesNotExist:
            return Response({"detail": "Line not found."}, status=status.HTTP_404_NOT_FOUND)

class IngredientNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient  # Make sure Ingredient is imported from inventory.models
        fields = ["id", "name", "unit_of_measure", "average_unit_cost"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    # Nested representation so line.ingredient.name and line.ingredient.average_unit_cost work on the frontend
    ingredient = IngredientNestedSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient", write_only=True
    )
    
    line_cost = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = [
            "id",
            "ingredient",
            "ingredient_id",
            "quantity",
            "line_cost",
        ]
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import RecipeForm, RecipeIngredientForm
from .models import Recipe, RecipeIngredient


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

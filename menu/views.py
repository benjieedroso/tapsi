from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import AddOnForm, CategoryForm, MenuItemForm
from .models import AddOn, Category, MenuItem, MenuItemAddOn, MenuItemPriceHistory


def _is_manager_or_above(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


def _restaurant_id(user):
    return user.restaurant_id


# ── Category Views (FR-030) ──────────────────────────────────────────


@user_passes_test(_is_manager_or_above)
def category_list(request):
    rid = _restaurant_id(request.user)
    categories = Category.objects.filter(restaurant_id=rid)
    return render(request, "menu/category_list.html", {"categories": categories})


@user_passes_test(_is_manager_or_above)
def category_create(request):
    rid = _restaurant_id(request.user)
    form = CategoryForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        cat = form.save(commit=False)
        cat.restaurant_id = rid
        cat.save()
        messages.success(request, f"Category \"{cat.name}\" created.")
        return redirect("menu:category_list")
    return render(request, "menu/category_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def category_edit(request, pk):
    rid = _restaurant_id(request.user)
    category = get_object_or_404(Category, pk=pk, restaurant_id=rid)
    form = CategoryForm(request.POST or None, instance=category, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Category \"{category.name}\" updated.")
        return redirect("menu:category_list")
    return render(request, "menu/category_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def category_delete(request, pk):
    rid = _restaurant_id(request.user)
    category = get_object_or_404(Category, pk=pk, restaurant_id=rid)
    # Unassign items before deleting category
    MenuItem.objects.filter(category=category).update(category=None)
    category.delete()
    messages.success(request, f"Category \"{category.name}\" deleted.")
    return redirect("menu:category_list")


# ── Menu Item Views (FR-031, FR-034, FR-035) ─────────────────────────


@user_passes_test(_is_manager_or_above)
def menu_list(request):
    rid = _restaurant_id(request.user)
    q = request.GET.get("q", "").strip()
    cat_id = request.GET.get("category", "")

    items = MenuItem.objects.filter(restaurant_id=rid, is_deleted=False)
    if q:
        items = items.filter(name__icontains=q)
    if cat_id:
        items = items.filter(category_id=cat_id)

    categories = Category.objects.filter(restaurant_id=rid)
    return render(request, "menu/menu_list.html", {
        "items": items,
        "categories": categories,
        "q": q,
        "selected_category": cat_id,
    })


@user_passes_test(_is_manager_or_above)
def menu_create(request):
    rid = _restaurant_id(request.user)
    form = MenuItemForm(request.POST or None, request.FILES or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.restaurant_id = rid
        item.save()
        messages.success(request, f"Menu item \"{item.name}\" created.")
        return redirect("menu:menu_list")
    return render(request, "menu/menu_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def menu_edit(request, pk):
    rid = _restaurant_id(request.user)
    item = get_object_or_404(MenuItem, pk=pk, restaurant_id=rid, is_deleted=False)
    form = MenuItemForm(
        request.POST or None, request.FILES or None,
        instance=item, restaurant_id=rid,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Menu item \"{item.name}\" updated.")
        return redirect("menu:menu_list")
    return render(request, "menu/menu_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def menu_delete(request, pk):
    """FR-035: Soft delete — item stays in historical records."""
    rid = _restaurant_id(request.user)
    item = get_object_or_404(MenuItem, pk=pk, restaurant_id=rid, is_deleted=False)
    item.soft_delete()
    messages.success(request, f"Menu item \"{item.name}\" deleted.")
    return redirect("menu:menu_list")


@user_passes_test(_is_manager_or_above)
@require_POST
def menu_toggle_availability(request, pk):
    """FR-034: Toggle availability without deleting."""
    rid = _restaurant_id(request.user)
    item = get_object_or_404(MenuItem, pk=pk, restaurant_id=rid, is_deleted=False)
    item.is_available = not item.is_available
    item.save(update_fields=["is_available"])
    status = "available" if item.is_available else "unavailable"
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"is_available": item.is_available})
    messages.success(request, f"\"{item.name}\" is now {status}.")
    return redirect("menu:menu_list")


# ── Price History (FR-036) ───────────────────────────────────────────


@user_passes_test(_is_manager_or_above)
def menu_price_history(request, pk):
    rid = _restaurant_id(request.user)
    item = get_object_or_404(MenuItem, pk=pk, restaurant_id=rid, is_deleted=False)
    history = item.price_history.select_related("changed_by").all()
    return render(request, "menu/price_history.html", {"item": item, "history": history})


# ── Add-On Views (FR-033) ────────────────────────────────────────────


@user_passes_test(_is_manager_or_above)
def addon_list(request):
    rid = _restaurant_id(request.user)
    addons = AddOn.objects.filter(restaurant_id=rid)
    return render(request, "menu/addon_list.html", {"addons": addons})


@user_passes_test(_is_manager_or_above)
def addon_create(request):
    rid = _restaurant_id(request.user)
    form = AddOnForm(request.POST or None, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        addon = form.save(commit=False)
        addon.restaurant_id = rid
        addon.save()
        messages.success(request, f"Add-on \"{addon.name}\" created.")
        return redirect("menu:addon_list")
    return render(request, "menu/addon_form.html", {"form": form, "action": "Create"})


@user_passes_test(_is_manager_or_above)
def addon_edit(request, pk):
    rid = _restaurant_id(request.user)
    addon = get_object_or_404(AddOn, pk=pk, restaurant_id=rid)
    form = AddOnForm(request.POST or None, instance=addon, restaurant_id=rid)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Add-on \"{addon.name}\" updated.")
        return redirect("menu:addon_list")
    return render(request, "menu/addon_form.html", {"form": form, "action": "Edit"})


@user_passes_test(_is_manager_or_above)
@require_POST
def addon_delete(request, pk):
    rid = _restaurant_id(request.user)
    addon = get_object_or_404(AddOn, pk=pk, restaurant_id=rid)
    addon.delete()
    messages.success(request, f"Add-on \"{addon.name}\" deleted.")
    return redirect("menu:addon_list")


@user_passes_test(_is_manager_or_above)
@require_POST
def menu_toggle_addon(request, menu_pk, addon_pk):
    """Toggle an add-on link for a menu item."""
    rid = _restaurant_id(request.user)
    item = get_object_or_404(MenuItem, pk=menu_pk, restaurant_id=rid, is_deleted=False)
    addon = get_object_or_404(AddOn, pk=addon_pk, restaurant_id=rid)
    link, created = MenuItemAddOn.objects.get_or_create(menu_item=item, addon=addon)
    if not created:
        link.delete()
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"attached": created})
    return redirect("menu:menu_edit", pk=menu_pk)

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
#DRF imports
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    AddOnSerializer,
    MenuItemPriceHistorySerializer,
)

from accounts.models import User

from .forms import AddOnForm, CategoryForm, MenuItemForm
from .models import Category, MenuItem, MenuItemPriceHistory, AddOn, MenuItemAddOn

User = get_user_model()

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


# ── DRF API ViewSets (Tenant-Isolated) ─────────────────────────────── #
class IsManagerOrOwner(permissions.BasePermission):
    """Custom DRF Permission restricting write operations to Managers and Owners."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in {User.Role.OWNER, User.Role.MANAGER}
        )


class TenantAwareViewSet(viewsets.ModelViewSet):
    """Base ViewSet enforcing tenant isolation and read/write permission splitting."""

    def get_permissions(self):
        # Allow any authenticated employee (Cashier, Staff, Manager, Owner) to GET data
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsManagerOrOwner()]

    def get_restaurant_id(self):
        return self.request.user.restaurant_id

    def perform_create(self, serializer):
        serializer.save(restaurant_id=self.get_restaurant_id())


class CategoryViewSet(TenantAwareViewSet):
    """API Endpoint for Category CRUD (FR-030)."""

    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(restaurant_id=self.get_restaurant_id())


class MenuItemViewSet(TenantAwareViewSet):
    """API Endpoint for MenuItem CRUD (FR-031, FR-034, FR-035, FR-036)."""

    serializer_class = MenuItemSerializer

    def get_queryset(self):
        queryset = MenuItem.objects.filter(
            restaurant_id=self.get_restaurant_id(), is_deleted=False
        )
        category_id = self.request.query_params.get("category")
        search = self.request.query_params.get("q")

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def perform_update(self, serializer):
        item = serializer.save()
        # Associate user who made the price update with price history log
        latest_history = MenuItemPriceHistory.objects.filter(menu_item=item).first()
        if latest_history and latest_history.changed_by is None:
            latest_history.changed_by = self.request.user
            latest_history.save(update_fields=["changed_by"])

    def perform_destroy(self, instance):
        # FR-035: Enforce soft delete
        instance.soft_delete()

    @action(detail=True, methods=["post"], url_path="toggle-availability")
    def toggle_availability(self, request, pk=None):
        """API Action: Toggle availability (FR-034)."""
        item = self.get_object()
        item.is_available = not item.is_available
        item.save(update_fields=["is_available"])
        return Response(
            {"id": item.id, "is_available": item.is_available},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="price-history")
    def price_history(self, request, pk=None):
        """API Action: Get price change logs (FR-036)."""
        item = self.get_object()
        history = item.price_history.all()
        serializer = MenuItemPriceHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="toggle-addon")
    def toggle_addon(self, request, pk=None):
        """API Action: Attach/Detach an AddOn from a MenuItem (FR-033)."""
        item = self.get_object()
        addon_id = request.data.get("addon_id")

        if not addon_id:
            return Response(
                {"error": "addon_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            addon = AddOn.objects.get(
                pk=addon_id, restaurant_id=self.get_restaurant_id()
            )
            link = MenuItemAddOn.objects.filter(menu_item=item, addon=addon).first()

            if link:
                link.delete()
                attached = False
            else:
                MenuItemAddOn.objects.create(menu_item=item, addon=addon)
                attached = True

            return Response(
                {"menu_item_id": item.id, "addon_id": addon.id, "attached": attached},
                status=status.HTTP_200_OK,
            )
        except AddOn.DoesNotExist:
            return Response(
                {"error": "AddOn not found in your restaurant."},
                status=status.HTTP_404_NOT_FOUND,
            )


class AddOnViewSet(TenantAwareViewSet):
    """API Endpoint for AddOn CRUD (FR-033)."""

    serializer_class = AddOnSerializer

    def get_queryset(self):
        return AddOn.objects.filter(restaurant_id=self.get_restaurant_id())
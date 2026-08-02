from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    # Categories (FR-030)
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    # Menu items (FR-031, FR-034, FR-035, FR-037)
    path("items/", views.menu_list, name="menu_list"),
    path("items/new/", views.menu_create, name="menu_create"),
    path("items/<int:pk>/edit/", views.menu_edit, name="menu_edit"),
    path("items/<int:pk>/delete/", views.menu_delete, name="menu_delete"),
    path("items/<int:pk>/toggle/", views.menu_toggle_availability, name="menu_toggle"),
    path("items/<int:pk>/price-history/", views.menu_price_history, name="menu_price_history"),
    path("items/<int:menu_pk>/addons/<int:addon_pk>/toggle/", views.menu_toggle_addon, name="menu_toggle_addon"),
    # Add-ons (FR-033)
    path("addons/", views.addon_list, name="addon_list"),
    path("addons/new/", views.addon_create, name="addon_create"),
    path("addons/<int:pk>/edit/", views.addon_edit, name="addon_edit"),
    path("addons/<int:pk>/delete/", views.addon_delete, name="addon_delete"),
]

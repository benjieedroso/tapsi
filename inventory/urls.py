from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Ingredients (FR-040, FR-041)
    path("ingredients/", views.ingredient_list, name="ingredient_list"),
    path("ingredients/new/", views.ingredient_create, name="ingredient_create"),
    path("ingredients/<int:pk>/edit/", views.ingredient_edit, name="ingredient_edit"),
    path("ingredients/<int:pk>/delete/", views.ingredient_delete, name="ingredient_delete"),
    # Stock card (FR-046)
    path("ingredients/<int:pk>/transactions/", views.stock_card, name="stock_card"),
    # Stock movement (FR-042)
    path("transactions/new/", views.transaction_create, name="transaction_create"),
]

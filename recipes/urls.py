from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "recipes"

router = DefaultRouter()
router.register(r"records", views.RecipeViewSet, basename="recipe")

urlpatterns = [
    # DRF API Routes -> /recipes/api/v1/records/
    path("api/v1/", include(router.urls)),
    #Legacy
    path("", views.recipe_list, name="recipe_list"),
    path("new/", views.recipe_create, name="recipe_create"),
    path("<int:pk>/", views.recipe_detail, name="recipe_detail"),
    path("<int:pk>/edit/", views.recipe_edit, name="recipe_edit"),
    path("<int:pk>/delete/", views.recipe_delete, name="recipe_delete"),
    path("<int:pk>/lines/add/", views.recipe_line_add, name="recipe_line_add"),
    path("<int:pk>/lines/<int:line_pk>/remove/", views.recipe_line_remove, name="recipe_line_remove"),
]

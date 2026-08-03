from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.recipe_list, name="recipe_list"),
    path("new/", views.recipe_create, name="recipe_create"),
    path("<int:pk>/", views.recipe_detail, name="recipe_detail"),
    path("<int:pk>/edit/", views.recipe_edit, name="recipe_edit"),
    path("<int:pk>/delete/", views.recipe_delete, name="recipe_delete"),
    path("<int:pk>/lines/add/", views.recipe_line_add, name="recipe_line_add"),
    path("<int:pk>/lines/<int:line_pk>/remove/", views.recipe_line_remove, name="recipe_line_remove"),
]

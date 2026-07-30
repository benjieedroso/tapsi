from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Restaurant, User


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_number", "is_vat_registered", "created_at")
    search_fields = ("name", "tin")


@admin.register(User)
class TAPSIUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("TAPSI", {"fields": ("restaurant", "role", "phone", "must_change_password")}),)
    list_display = ("email", "first_name", "last_name", "restaurant", "role", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")

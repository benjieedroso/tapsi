from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Restaurant, StaffAudit, User


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_number", "is_vat_registered", "created_at")
    search_fields = ("name", "tin")


@admin.register(User)
class TAPSIUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("TAPSI", {"fields": ("restaurant", "role", "phone", "must_change_password", "is_deleted", "deleted_at")}),)
    list_display = ("email", "first_name", "last_name", "restaurant", "role", "is_active", "is_deleted")
    list_filter = ("role", "is_active", "is_deleted")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")


@admin.register(StaffAudit)
class StaffAuditAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target", "restaurant", "created_at")
    list_filter = ("action",)
    search_fields = ("actor__email", "target__email", "restaurant__name")
    readonly_fields = ("restaurant", "actor", "target", "action", "detail", "ip_address", "user_agent", "created_at")

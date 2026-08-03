from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "entity", "entity_id", "restaurant_id")
    list_filter = ("action", "entity")
    date_hierarchy = "created_at"
    search_fields = ("actor__email", "entity_id")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "restaurant_id", "target_role", "user", "read_at", "created_at")
    list_filter = ("type", "target_role")
    date_hierarchy = "created_at"

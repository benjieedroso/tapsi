from django.contrib import admin

from .models import DailyClosing


@admin.register(DailyClosing)
class DailyClosingAdmin(admin.ModelAdmin):
    list_display = ("business_date", "restaurant_id", "status", "expected_cash", "counted_cash", "variance", "closed_by")
    list_filter = ("status",)
    date_hierarchy = "business_date"

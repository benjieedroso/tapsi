from django.contrib import admin

from .models import AddOn, Category, MenuItem, MenuItemAddOn, MenuItemPriceHistory


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant_id", "display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant_id", "category", "price", "is_available", "is_deleted")
    list_filter = ("is_available", "is_deleted")
    search_fields = ("name",)


class AddOnAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant_id", "price", "is_available")
    search_fields = ("name",)


class MenuItemPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "old_price", "new_price", "changed_by", "created_at")
    readonly_fields = ("menu_item", "old_price", "new_price", "changed_by", "created_at")


class MenuItemAddOnAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "addon")


admin.site.register(Category, CategoryAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(AddOn, AddOnAdmin)
admin.site.register(MenuItemPriceHistory, MenuItemPriceHistoryAdmin)
admin.site.register(MenuItemAddOn, MenuItemAddOnAdmin)

from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("expense_date", "category", "amount", "payee", "status", "created_by")
    list_filter = ("category", "status", "expense_date")
    date_hierarchy = "expense_date"

from django.contrib import admin

from .models import Attendance, Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "position", "employment_status", "date_hired", "restaurant_id")
    list_filter = ("employment_status",)
    search_fields = ("full_name", "position")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "work_date", "clock_in", "clock_out")
    date_hierarchy = "work_date"

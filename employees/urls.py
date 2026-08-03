from django.urls import path

from . import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list, name="employee_list"),
    path("new/", views.employee_create, name="employee_create"),
    path("<int:pk>/edit/", views.employee_edit, name="employee_edit"),
    path("<int:pk>/delete/", views.employee_delete, name="employee_delete"),
    path("attendance/", views.attendance_list, name="attendance_list"),
    path("attendance/clock/", views.attendance_clock, name="attendance_clock"),
    path("attendance/<int:pk>/edit/", views.attendance_edit, name="attendance_edit"),
]

from django.urls import path

from . import views

app_name = "closing"

urlpatterns = [
    path("", views.closing_list, name="closing_list"),
    path("prepare/", views.closing_prepare, name="closing_prepare"),
    path("complete/", views.closing_complete, name="closing_complete"),
    path("report/<int:pk>/", views.eod_report, name="eod_report"),
    path("<int:pk>/reopen/", views.closing_reopen, name="closing_reopen"),
]

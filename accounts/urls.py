from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("api/token/", views.api_token, name="api_token"),
    path("api/token/refresh/", views.api_token_refresh, name="api_token_refresh"),
    path("api/token/logout/", views.api_token_logout, name="api_token_logout"),
    path("register/", views.register, name="register"),
    path("login/", views.TAPSILoginView.as_view(), name="login"),
    path("logout/", views.logout, name="logout"),
    path("change-initial-password/", views.change_initial_password, name="change_initial_password"),
    path("password/change/", views.change_password, name="change_password"),
    path("password/reset/", views.TAPSPasswordResetView.as_view(), name="password_reset"),
    path("password/reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", views.TAPSPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("profile/", views.profile, name="profile"),
    path("profile/email/", views.request_email_change, name="request_email_change"),
    path("profile/email/verify/<uidb64>/<token>/", views.verify_email_change, name="verify_email"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/new/", views.create_staff, name="create_staff"),
]

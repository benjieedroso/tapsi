from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from . import views

app_name = "accounts"

router = DefaultRouter()
router.register(r"restaurants", views.RestaurantViewSet, basename="restaurant")
router.register(r"staff", views.StaffViewSet, basename="staff")

urlpatterns = [
    # JWT Authentication Endpoints
    path("auth/token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.CurrentUserView.as_view(), name="current_user"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    # Password Flow
    path("auth/password/change/", views.ChangePasswordView.as_view(), name="change_password"),
    path("auth/password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("auth/password/reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # Profile Update
    path("profile/email/", views.RequestEmailChangeView.as_view(), name="request_email_change"),
    # Account / Restaurant Management APIs
    path("", include(router.urls)),


    # Legacy Code
    # path("api/token/", views.api_token, name="api_token"),
    # path("api/token/refresh/", views.api_token_refresh, name="api_token_refresh"),
    # path("api/token/logout/", views.api_token_logout, name="api_token_logout"),
    # path("register/", views.register, name="register"),
    # path("login/", views.TAPSILoginView.as_view(), name="login"),
    # path("logout/", views.logout, name="logout"),
    # path("change-initial-password/", views.change_initial_password, name="change_initial_password"),
    # path("password/change/", views.change_password, name="change_password"),
    # path("password/reset/", views.TAPSPasswordResetView.as_view(), name="password_reset"),
    # path("password/reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    # path("password/reset/<uidb64>/<token>/", views.TAPSPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # path("profile/", views.profile, name="profile"),
    # path("profile/email/", views.request_email_change, name="request_email_change"),
    # path("profile/email/verify/<uidb64>/<token>/", views.verify_email_change, name="verify_email"),
    # path("staff/", views.staff_list, name="staff_list"),
    # path("staff/new/", views.create_staff, name="create_staff"),
    # path("staff/<int:user_id>/edit/", views.staff_edit, name="staff_edit"),
    # path("staff/<int:user_id>/reset-password/", views.staff_reset_password, name="staff_reset_password"),
    # path("settings/", views.restaurant_settings, name="restaurant_settings"),
]

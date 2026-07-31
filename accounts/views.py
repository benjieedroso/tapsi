from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from .forms import (
    CurrentPasswordChangeForm, EmailAuthenticationForm, EmailChangeForm,
    FirstPasswordChangeForm, ProfileForm, RegistrationForm, StaffUserForm,
)
from .models import AuthenticationAudit, User
from .services import (
    JWTError, audit_authentication, invalidate_other_sessions, is_locked,
    issue_token_pair, revoke_all_refresh_tokens, revoke_refresh_token, rotate_refresh_token,
)


def _json_body(request):
    import json
    try:
        return json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def api_token(request):
    """Issue a 15-minute access token and rotating 7-day refresh token."""
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    data = _json_body(request)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "A JSON object is required."}, status=400)
    email = str(data.get("email", "")).lower().strip()
    password = data.get("password", "")
    user = User.objects.filter(email__iexact=email).first()
    if not user or not user.is_active or is_locked(user) or not user.check_password(password):
        audit_authentication(request, AuthenticationAudit.Action.LOGIN_FAILURE, user=user, email=email)
        if user and user.is_active and not is_locked(user):
            user.failed_login_count += 1
            fields = ["failed_login_count"]
            if user.failed_login_count >= 5:
                user.failed_login_count = 0
                user.locked_until = timezone.now() + timedelta(minutes=15)
                fields.extend(["failed_login_count", "locked_until"])
                audit_authentication(request, AuthenticationAudit.Action.ACCOUNT_LOCKED, user=user)
            user.save(update_fields=fields)
        return JsonResponse({"detail": "Unable to log in with the provided credentials."}, status=401)
    user.failed_login_count = 0
    user.locked_until = None
    user.save(update_fields=["failed_login_count", "locked_until"])
    audit_authentication(request, AuthenticationAudit.Action.LOGIN_SUCCESS, user=user)
    return JsonResponse(issue_token_pair(user))


def api_token_refresh(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    data = _json_body(request)
    try:
        return JsonResponse(rotate_refresh_token(data["refresh"]))
    except (TypeError, KeyError, JWTError):
        return JsonResponse({"detail": "Invalid or expired refresh token."}, status=401)


def api_token_logout(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    data = _json_body(request)
    try:
        revoke_refresh_token(data["refresh"])
    except (TypeError, KeyError, JWTError):
        return JsonResponse({"detail": "Invalid or expired refresh token."}, status=401)
    return JsonResponse({}, status=204)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        audit_authentication(request, AuthenticationAudit.Action.LOGIN_SUCCESS, user=user)
        messages.success(request, f"Welcome to TAPSI, {user.display_name}.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


class TAPSILoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": EmailAuthenticationForm(request=request)})

    def post(self, request):
        form = EmailAuthenticationForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            if is_locked(user):
                audit_authentication(request, AuthenticationAudit.Action.LOGIN_FAILURE, user=user)
                form.add_error(None, "Unable to log in with the provided credentials.")
            else:
                user.failed_login_count = 0
                user.locked_until = None
                user.save(update_fields=["failed_login_count", "locked_until"])
                login(request, user)
                audit_authentication(request, AuthenticationAudit.Action.LOGIN_SUCCESS, user=user)
                return redirect("accounts:change_initial_password" if user.must_change_password else "dashboard")
        else:
            email = form.data.get("email", "").lower().strip()
            user = User.objects.filter(email__iexact=email).first()
            audit_authentication(request, AuthenticationAudit.Action.LOGIN_FAILURE, user=user, email=email)
            if user and user.is_active and not is_locked(user):
                user.failed_login_count += 1
                update_fields = ["failed_login_count"]
                if user.failed_login_count >= 5:
                    user.locked_until = timezone.now() + timedelta(minutes=15)
                    user.failed_login_count = 0
                    update_fields.extend(["locked_until", "failed_login_count"])
                    audit_authentication(request, AuthenticationAudit.Action.ACCOUNT_LOCKED, user=user)
                user.save(update_fields=update_fields)
        return render(request, self.template_name, {"form": form}, status=400)


@login_required
def logout(request):
    if request.method != "POST":
        return redirect("dashboard")
    audit_authentication(request, AuthenticationAudit.Action.LOGOUT, user=request.user)
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def change_initial_password(request):
    if not request.user.must_change_password:
        return redirect("dashboard")
    form = FirstPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])
        update_session_auth_hash(request, user)
        invalidate_other_sessions(user, request.session.session_key)
        revoke_all_refresh_tokens(user)
        audit_authentication(request, AuthenticationAudit.Action.PASSWORD_CHANGED, user=user)
        messages.success(request, "Your password has been updated.")
        return redirect("dashboard")
    return render(request, "accounts/change_initial_password.html", {"form": form})


@login_required
def change_password(request):
    form = CurrentPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        invalidate_other_sessions(user, request.session.session_key)
        revoke_all_refresh_tokens(user)
        audit_authentication(request, AuthenticationAudit.Action.PASSWORD_CHANGED, user=user)
        messages.success(request, "Your password has been changed. Other sessions were signed out.")
        return redirect("accounts:profile")
    return render(request, "accounts/change_password.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def request_email_change(request):
    form = EmailChangeForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        user = request.user
        user.pending_email = form.cleaned_data["email"]
        user.save(update_fields=["pending_email"])
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_url = request.build_absolute_uri(reverse("accounts:verify_email", args=[uid, token]))
        send_mail("Confirm your new TAPSI email", f"Confirm your new email address: {verification_url}", None, [user.pending_email])
        audit_authentication(request, AuthenticationAudit.Action.EMAIL_CHANGE_REQUESTED, user=user)
        messages.success(request, "A confirmation link was sent to your new email address.")
        return redirect("accounts:profile")
    return render(request, "accounts/email_change.html", {"form": form})


def verify_email_change(request, uidb64, token):
    try:
        user = User.objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user and user.pending_email and default_token_generator.check_token(user, token):
        user.email = user.pending_email
        user.username = user.pending_email
        user.pending_email = ""
        user.save(update_fields=["email", "username", "pending_email"])
        audit_authentication(request, AuthenticationAudit.Action.EMAIL_CHANGED, user=user)
        messages.success(request, "Your email address has been verified and updated. Please log in again.")
        return redirect("accounts:login")
    messages.error(request, "That email confirmation link is invalid or has expired.")
    return redirect("accounts:login")


class TAPSPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/email/password_reset_email.txt"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class TAPSPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_other_sessions(form.user)
        revoke_all_refresh_tokens(form.user)
        audit_authentication(self.request, AuthenticationAudit.Action.PASSWORD_RESET, user=form.user)
        messages.success(self.request, "Your password has been reset. Please log in.")
        return response


@login_required
def dashboard(request):
    if request.user.must_change_password:
        return redirect("accounts:change_initial_password")
    return render(request, "dashboard.html")


def can_manage_staff(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


@user_passes_test(can_manage_staff)
def create_staff(request):
    form = StaffUserForm(request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        member = form.save()
        messages.success(request, f"Created {member.display_name}'s staff account.")
        return redirect("accounts:staff_list")
    return render(request, "accounts/staff_form.html", {"form": form})


@user_passes_test(can_manage_staff)
def staff_list(request):
    staff = request.user.restaurant.users.order_by("role", "first_name", "email")
    return render(request, "accounts/staff_list.html", {"staff": staff})

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class Restaurant(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    tin = models.CharField(max_length=30, blank=True)
    is_vat_registered = models.BooleanField(default=False)
    receipt_footer = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=50, default="Asia/Manila", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.OWNER)
        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError("Superusers must have is_staff=True and is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Cashier"
        KITCHEN = "KITCHEN", "Kitchen"

    username = models.CharField(max_length=254, unique=True, editable=False)
    email = models.EmailField(unique=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name="users", null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CASHIER)
    phone = models.CharField(max_length=30, blank=True, validators=[RegexValidator(r"^[0-9+() -]*$", "Enter a valid phone number.")])
    avatar = models.FileField(upload_to="avatars/", blank=True)
    must_change_password = models.BooleanField(default=False)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    pending_email = models.EmailField(blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []
    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=["restaurant", "role"]),
            models.Index(fields=["restaurant", "is_active", "is_deleted"]),
        ]

    @property
    def display_name(self):
        return self.get_full_name() or self.email

    def soft_delete(self):
        from django.utils import timezone as tz
        self.is_deleted = True
        self.deleted_at = tz.now()
        self.is_active = False
        self.save(update_fields=["is_deleted", "deleted_at", "is_active"])

    def __str__(self):
        return self.email


class StaffAudit(models.Model):
    class Action(models.TextChoices):
        ROLE_CHANGED = "ROLE_CHANGED", "Role changed"
        DEACTIVATED = "DEACTIVATED", "Account deactivated"
        ACTIVATED = "ACTIVATED", "Account activated"
        SOFT_DELETED = "SOFT_DELETED", "Account soft-deleted"
        PASSWORD_RESET = "PASSWORD_RESET", "Password reset by admin"
        PROFILE_UPDATED = "PROFILE_UPDATED", "Profile updated by admin"

    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name="staff_audits")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="staff_actions_performed")
    target = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="staff_actions_received")
    action = models.CharField(max_length=20, choices=Action.choices)
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["restaurant", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action}: {self.target} by {self.actor}"


class AuthenticationAudit(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login successful"
        LOGIN_FAILURE = "LOGIN_FAILURE", "Login failed"
        LOGOUT = "LOGOUT", "Logged out"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password changed"
        PASSWORD_RESET = "PASSWORD_RESET", "Password reset"
        ACCOUNT_LOCKED = "ACCOUNT_LOCKED", "Account locked"
        EMAIL_CHANGE_REQUESTED = "EMAIL_CHANGE_REQUESTED", "Email change requested"
        EMAIL_CHANGED = "EMAIL_CHANGED", "Email changed"

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="authentication_audits")
    email = models.EmailField(blank=True)
    action = models.CharField(max_length=30, choices=Action.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.action}: {self.email}"


class RefreshToken(models.Model):
    """Server-side refresh-token registry used for rotation and revocation."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    jti = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("user", "revoked_at"))]

    @property
    def is_active(self):
        from django.utils import timezone
        return self.revoked_at is None and self.expires_at > timezone.now()

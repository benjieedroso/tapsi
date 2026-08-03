from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """FR-150..FR-153: in-app notifications, role- or user-addressed."""
    class Type(models.TextChoices):
        LOW_STOCK = "LOW_STOCK", "Low stock"
        NEW_ORDER = "NEW_ORDER", "New order"
        ORDER_CANCELLED = "ORDER_CANCELLED", "Order cancelled"
        LARGE_DISCOUNT = "LARGE_DISCOUNT", "Large discount"
        CLOSING_REMINDER = "CLOSING_REMINDER", "Closing reminder"
        PO_RECEIVED = "PO_RECEIVED", "PO received"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=120)
    body = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    target_role = models.CharField(max_length=20, blank=True)  # FR-151: role-addressed
    user = models.ForeignKey(  # FR-151: user-addressed
        "accounts.User", on_delete=models.CASCADE, null=True, blank=True,
        related_name="notifications",
    )
    read_at = models.DateTimeField(null=True, blank=True)  # FR-152
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

    @property
    def unread(self):
        return self.read_at is None

    def mark_read(self):
        if self.unread:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])

    @classmethod
    def for_user(cls, user):
        """FR-151: role-addressed + user-addressed, scoped to restaurant."""
        return cls.objects.filter(
            restaurant_id=user.restaurant_id,
        ).filter(
            models.Q(user=user) | models.Q(user__isnull=True, target_role=user.role),
        )

    @classmethod
    def unread_count(cls, user):
        return cls.for_user(user).filter(read_at__isnull=True).count()

    @classmethod
    def purge_old(cls):
        """FR-153: notifications older than 90 days are purged."""
        cutoff = timezone.now() - timezone.timedelta(days=90)
        deleted, _ = cls.objects.filter(created_at__lt=cutoff).delete()
        return deleted

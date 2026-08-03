from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """FR-160..FR-163: append-only audit trail. Entries must never be
    modified or deleted (delete() raises)."""
    restaurant_id = models.PositiveIntegerField(db_index=True, null=True, blank=True)
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_entries",
    )
    actor_role = models.CharField(max_length=20, blank=True)
    action = models.CharField(max_length=50, db_index=True)
    entity = models.CharField(max_length=50, db_index=True)
    entity_id = models.PositiveBigIntegerField(null=True, blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} {self.entity}#{self.entity_id}"

    def delete(self, *args, **kwargs):
        raise NotImplementedError("FR-162: audit logs are append-only and cannot be deleted.")

    @classmethod
    def scoped(cls, restaurant_id):
        """FR-163: Managers read logs of their own restaurant only."""
        return cls.objects.filter(restaurant_id=restaurant_id)

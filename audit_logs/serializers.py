from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.ReadOnlyField(source="actor.get_full_name")
    actor_email = serializers.ReadOnlyField(source="actor.email")

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "restaurant_id",
            "actor",
            "actor_name",
            "actor_email",
            "actor_role",
            "action",
            "entity",
            "entity_id",
            "before",
            "after",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = fields
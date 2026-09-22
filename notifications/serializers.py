from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    unread = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "restaurant_id",
            "type",
            "type_display",
            "title",
            "body",
            "link",
            "target_role",
            "user",
            "unread",
            "read_at",
            "created_at",
        ]
        read_only_fields = [
            "restaurant_id",
            "read_at",
            "created_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        restaurant_id = getattr(request.user, "restaurant_id", None)
        return Notification.objects.create(restaurant_id=restaurant_id, **validated_data)
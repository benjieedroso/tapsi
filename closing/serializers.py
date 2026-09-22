from django.utils import timezone
from rest_framework import serializers
from .models import DailyClosing


class DailyClosingSerializer(serializers.ModelSerializer):
    closed_by_name = serializers.ReadOnlyField(source="closed_by.get_full_name")
    reopened_by_name = serializers.ReadOnlyField(source="reopened_by.get_full_name")

    class Meta:
        model = DailyClosing
        fields = [
            "id",
            "restaurant_id",
            "business_date",
            "opening_float",
            "expected_cash",
            "counted_cash",
            "variance",
            "variance_note",
            "status",
            "closed_by",
            "closed_by_name",
            "reopened_by",
            "reopened_by_name",
            "reopen_reason",
            "reopened_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "restaurant_id",
            "opening_float",
            "expected_cash",
            "variance",
            "status",
            "closed_by",
            "reopened_by",
            "reopened_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        restaurant_id = getattr(request.user, "restaurant_id", None)
        user = request.user if request and request.user.is_authenticated else None

        business_date = validated_data.get("business_date")
        counted_cash = validated_data.get("counted_cash", 0)

        # FR-140 / FR-145: Compute expected balances dynamically
        opening_float = DailyClosing.current_float(restaurant_id)
        expected_cash = DailyClosing.expected_cash_for(restaurant_id, business_date)
        variance = counted_cash - expected_cash

        return DailyClosing.objects.create(
            restaurant_id=restaurant_id,
            opening_float=opening_float,
            expected_cash=expected_cash,
            variance=variance,
            status=DailyClosing.Status.CLOSED,
            closed_by=user,
            **validated_data
        )


class ReopenDaySerializer(serializers.Serializer):
    reopen_reason = serializers.CharField(max_length=255, required=True)
from rest_framework import serializers
from accounts.models import User
from .models import Attendance, Employee


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source="employee.full_name")
    hours = serializers.ReadOnlyField()

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "employee_name",
            "work_date",
            "clock_in",
            "clock_out",
            "hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        clock_in = attrs.get("clock_in") or getattr(self.instance, "clock_in", None)
        clock_out = attrs.get("clock_out") or getattr(self.instance, "clock_out", None)

        if clock_in and clock_out and clock_out < clock_in:
            raise serializers.ValidationError({"clock_out": "Clock-out cannot be before clock-in."})

        return attrs


class EmployeeSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Employee
        fields = [
            "id",
            "full_name",
            "nickname",
            "phone",
            "address",
            "emergency_contact",
            "position",
            "employment_status",
            "date_hired",
            "daily_rate",
            "monthly_salary",
            "user",
            "user_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def to_representation(self, instance):
        """FR-121: Salary info is Owner/Manager-visible only."""
        data = super().to_representation(instance)
        request = self.context.get("request")

        if request and hasattr(request, "user"):
            user = request.user
            is_manager_or_owner = user.is_authenticated and user.role in {
                User.Role.OWNER,
                User.Role.MANAGER,
            }
            if not is_manager_or_owner:
                data.pop("daily_rate", None)
                data.pop("monthly_salary", None)

        return data
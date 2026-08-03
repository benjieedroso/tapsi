from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User

from .models import Attendance, Employee

MAX_FULL_NAME = 120
MAX_POSITION = 80


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class EmployeeForm(StyledFormMixin, forms.ModelForm):
    user_link = forms.ModelChoiceField(
        queryset=User.objects.none(), required=False, label="Linked User Account",
    )

    class Meta:
        model = Employee
        fields = (
            "full_name", "nickname", "phone", "address", "emergency_contact",
            "position", "employment_status", "date_hired",
            "daily_rate", "monthly_salary",
        )
        labels = {
            "employment_status": "Employment Status",
            "date_hired": "Date Hired",
            "daily_rate": "Daily Rate (₱)",
            "monthly_salary": "Monthly Salary (₱)",
        }
        widgets = {
            "date_hired": forms.DateInput(attrs={"type": "date"}),
            "daily_rate": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "monthly_salary": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        # FR-121: salary visible only to Owner/Manager.
        self.salary_visible = kwargs.get("initial", {}).get("_salary_visible", True)
        self.fields["user_link"].queryset = User.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False,
        ).exclude(employee_profile__isnull=False)
        self._apply_classes()

    def clean_full_name(self):
        value = self.cleaned_data.get("full_name", "")
        if not value or not value.strip():
            raise ValidationError("Full name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Full name must be at least 2 characters.")
        if len(value.strip()) > MAX_FULL_NAME:
            raise ValidationError(f"Full name must be {MAX_FULL_NAME} characters or fewer.")
        return value.strip()

    def clean_position(self):
        value = self.cleaned_data.get("position", "").strip()
        if len(value) > MAX_POSITION:
            raise ValidationError(f"Position must be {MAX_POSITION} characters or fewer.")
        return value

    def save(self, commit=True):
        employee = super().save(commit=False)
        if "user_link" in self.cleaned_data and self.cleaned_data["user_link"]:
            employee.user = self.cleaned_data["user_link"]
        if commit:
            employee.save()
        return employee


class AttendanceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ("employee", "work_date", "clock_in", "clock_out")
        labels = {
            "work_date": "Date",
        }
        widgets = {
            "work_date": forms.DateInput(attrs={"type": "date"}),
            "clock_in": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "clock_out": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = Employee.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False,
        ).order_by("full_name")
        self._apply_classes()

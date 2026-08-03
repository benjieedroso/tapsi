from django import forms
from django.core.exceptions import ValidationError

from .models import Expense

MAX_PAYEE = 120


def validate_receipt_image(upload):
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError("Receipt images must be 5 MB or smaller.")
    if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class ExpenseForm(StyledFormMixin, forms.ModelForm):
    receipt_image = forms.FileField(required=False, validators=[validate_receipt_image])

    class Meta:
        model = Expense
        fields = (
            "category", "amount", "expense_date", "payee",
            "payment_method", "notes", "receipt_image",
        )
        labels = {
            "expense_date": "Date",
            "payment_method": "Payment Method",
        }
        widgets = {
            "expense_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError("Amount is required.")
        if value <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return value

    def clean_payee(self):
        value = self.cleaned_data.get("payee", "").strip()
        if len(value) > MAX_PAYEE:
            raise ValidationError(f"Payee must be {MAX_PAYEE} characters or fewer.")
        return value

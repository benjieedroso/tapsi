from django import forms
from django.core.exceptions import ValidationError

from inventory.models import Ingredient

from .models import PurchaseOrder, PurchaseOrderItem, Supplier, SupplierPayment

MAX_SUPPLIER_NAME = 120
MAX_PERSON = 120
MAX_NOTES = 1000


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class SupplierForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = (
            "name", "contact_person", "phone", "email",
            "address", "payment_terms", "is_active",
        )
        labels = {
            "contact_person": "Contact Person",
            "payment_terms": "Payment Terms",
            "is_active": "Active",
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Supplier name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Supplier name must be at least 2 characters.")
        if len(value.strip()) > MAX_SUPPLIER_NAME:
            raise ValidationError(f"Supplier name must be {MAX_SUPPLIER_NAME} characters or fewer.")
        qs = Supplier.objects.filter(
            restaurant_id=self.restaurant_id,
            name__iexact=value.strip(),
            is_deleted=False,
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A supplier with this name already exists.")
        return value.strip()


class PurchaseOrderForm(StyledFormMixin, forms.ModelForm):
    """FR-060: header + dynamic line items (ingredient, quantity, unit cost)."""

    class Meta:
        model = PurchaseOrder
        fields = ("supplier", "expected_date", "notes")
        labels = {
            "expected_date": "Expected Delivery",
        }
        widgets = {
            "expected_date": forms.DateInput(attrs={"type": "date"}),
        }

    line_ingredient = forms.ModelChoiceField(
        queryset=None,
        label="Ingredient",
        required=False,
    )
    line_quantity = forms.DecimalField(
        max_digits=12, decimal_places=3, min_value=0.001,
        required=False, label="Qty",
    )
    line_unit_cost = forms.DecimalField(
        max_digits=12, decimal_places=4, min_value=0,
        required=False, label="Unit Cost",
    )

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(
            restaurant_id=restaurant_id,
            is_active=True,
            is_deleted=False,
        )
        self.fields["line_ingredient"].queryset = Ingredient.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False
        ).order_by("name")
        self._apply_classes()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("line_ingredient") is not None:
            if cleaned.get("line_quantity") is None:
                self.add_error("line_quantity", "Quantity is required for the line item.")
            if cleaned.get("line_unit_cost") is None:
                self.add_error("line_unit_cost", "Unit cost is required for the line item.")
        return cleaned

    def save(self, commit=True):
        po = super().save(commit=False)
        if commit:
            po.save()
        return po


class SupplierPaymentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ("amount", "payment_date", "method", "reference_no", "notes")
        labels = {
            "reference_no": "Reference Number",
        }
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is not None and value <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        return value

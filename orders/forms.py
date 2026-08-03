from django import forms
from django.core.exceptions import ValidationError

from menu.models import AddOn, MenuItem

from .models import DiningTable, Order, OrderItem, Payment


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class TableForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DiningTable
        fields = ("name", "seating_capacity", "is_active")
        labels = {
            "name": "Table Name/Number",
            "seating_capacity": "Seating Capacity",
            "is_active": "Active",
        }
        widgets = {
            "seating_capacity": forms.NumberInput(attrs={"min": "1", "style": "max-width: 100px;"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Table name cannot be blank.")
        if len(value.strip()) < 1 or len(value.strip()) > 40:
            raise ValidationError("Table name must be 1–40 characters.")
        qs = DiningTable.objects.filter(restaurant_id=self.restaurant_id, name__iexact=value.strip())
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A table with this name already exists.")
        return value.strip()

    def clean_seating_capacity(self):
        value = self.cleaned_data.get("seating_capacity", 2)
        if value < 1:
            raise ValidationError("Seating capacity must be at least 1.")
        return value


class OrderForm(StyledFormMixin, forms.Form):
    """FR-080: DINE_IN (table required), TAKE_OUT, DELIVERY (customer required)."""
    order_type = forms.ChoiceField(
        choices=Order.Type.choices, label="Order Type", initial=Order.Type.DINE_IN,
    )
    table = forms.ModelChoiceField(
        queryset=DiningTable.objects.none(), required=False, label="Table",
    )
    customer_name = forms.CharField(max_length=120, required=False, label="Customer Name")
    customer_phone = forms.CharField(max_length=30, required=False, label="Customer Phone")
    customer_address = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), max_length=500,
        required=False, label="Delivery Address",
    )

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["table"].queryset = DiningTable.objects.filter(
            restaurant_id=restaurant_id,
            status=DiningTable.Status.AVAILABLE,
            is_active=True,
        ).order_by("name")
        self.fields["table"].empty_label = "— Select available table —"
        self._apply_classes()

    def clean(self):
        cleaned = super().clean()
        order_type = cleaned.get("order_type")
        table = cleaned.get("table")
        if order_type == Order.Type.DINE_IN and table is None:
            self.add_error("table", "A table is required for dine-in orders (FR-080).")
        if order_type == Order.Type.DELIVERY:
            if not (cleaned.get("customer_name") or "").strip():
                self.add_error("customer_name", "Customer name is required for delivery orders.")
            if not (cleaned.get("customer_phone") or "").strip():
                self.add_error("customer_phone", "Customer phone is required for delivery orders.")
            if not (cleaned.get("customer_address") or "").strip():
                self.add_error("customer_address", "Delivery address is required for delivery orders.")
        return cleaned


class OrderItemForm(StyledFormMixin, forms.ModelForm):
    addons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple, label="Add-Ons",
    )

    class Meta:
        model = OrderItem
        fields = ("menu_item", "quantity", "notes")
        labels = {
            "menu_item": "Menu Item",
            "quantity": "Quantity",
            "notes": "Item Notes",
        }
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": "1", "style": "max-width: 100px;"}),
            "notes": forms.TextInput(attrs={"placeholder": "e.g., no onions"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["menu_item"].queryset = MenuItem.objects.filter(
            restaurant_id=restaurant_id, is_deleted=False, is_available=True,
        ).select_related("category").order_by("name")
        self.fields["addons"].queryset = AddOn.objects.filter(
            restaurant_id=restaurant_id, is_available=True,
        ).order_by("name")
        self._apply_classes()

    def clean_quantity(self):
        value = self.cleaned_data.get("quantity")
        if value is None or value < 1:
            raise ValidationError("Quantity must be at least 1 (FR-082).")
        return value


class DiscountForm(StyledFormMixin, forms.Form):
    """FR-087: Senior/PWD 20% VAT-exempt with ID; manual % (approval >10%)."""
    discount_type = forms.ChoiceField(choices=Order.DiscountType.choices, label="Discount Type")
    discount_ref = forms.CharField(
        max_length=40, required=False, label="ID Number",
        help_text="Required for Senior Citizen (RA 9994) and PWD (RA 10754).",
    )
    manual_discount_pct = forms.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100,
        required=False, label="Manual Discount %",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()


class PaymentForm(StyledFormMixin, forms.Form):
    """FR-100/FR-101: split payments; non-cash needs reference; cash may
    overpay with tendered amount for change."""
    method = forms.ChoiceField(choices=Payment.Method.choices, label="Method")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01, label="Amount")
    tendered = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False,
        label="Amount Tendered (cash)",
        help_text="Used to compute change.",
    )
    reference_no = forms.CharField(
        max_length=60, required=False, label="Reference Number",
        help_text="Required for GCash, Card, and Bank Transfer.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()


class RefundForm(StyledFormMixin, forms.Form):
    reason = forms.CharField(
        max_length=255, widget=forms.Textarea(attrs={"rows": 2}), label="Refund Reason",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()

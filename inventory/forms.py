from django import forms
from django.core.exceptions import ValidationError

from .models import Ingredient, InventoryTransaction

MAX_INGREDIENT_NAME = 100
MAX_REASON_LENGTH = 500
MAX_REFERENCE_LENGTH = 100


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class IngredientForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = (
            "name",
            "unit_of_measure",
            "minimum_stock",
            "average_unit_cost",
            "default_supplier_id",
        )
        labels = {
            "name": "Ingredient Name",
            "unit_of_measure": "Unit of Measure",
            "minimum_stock": "Minimum Stock",
            "average_unit_cost": "Average Unit Cost (₱)",
            "default_supplier_id": "Default Supplier ID",
        }
        help_texts = {
            "average_unit_cost": "Recalculated automatically as a weighted average on every purchase.",
            "default_supplier_id": "Supplier module is not live yet — enter the supplier ID here.",
        }
        widgets = {
            "minimum_stock": forms.NumberInput(attrs={"step": "0.01", "min": "0", "style": "max-width: 140px;"}),
            "average_unit_cost": forms.NumberInput(attrs={"step": "0.01", "min": "0", "style": "max-width: 140px;"}),
            "default_supplier_id": forms.NumberInput(attrs={"min": "0", "style": "max-width: 140px;"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Ingredient name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Ingredient name must be at least 2 characters.")
        if len(value.strip()) > MAX_INGREDIENT_NAME:
            raise ValidationError(f"Ingredient name must be {MAX_INGREDIENT_NAME} characters or fewer.")
        # Unique per restaurant (excluding soft-deleted ingredients).
        qs = Ingredient.objects.filter(
            restaurant_id=self.restaurant_id,
            name__iexact=value.strip(),
            is_deleted=False,
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("An ingredient with this name already exists.")
        return value.strip()

    def clean_minimum_stock(self):
        value = self.cleaned_data.get("minimum_stock", 0)
        if value is not None and value < 0:
            raise ValidationError("Minimum stock cannot be negative.")
        return value if value is not None else 0

    def clean_average_unit_cost(self):
        value = self.cleaned_data.get("average_unit_cost", 0)
        if value is not None and value < 0:
            raise ValidationError("Average unit cost cannot be negative.")
        return value if value is not None else 0

    def clean_default_supplier_id(self):
        value = self.cleaned_data.get("default_supplier_id")
        if value is not None and value < 0:
            raise ValidationError("Supplier ID cannot be negative.")
        return value


class IngredientTransactionForm(StyledFormMixin, forms.Form):
    """FR-042: PURCHASE / CONSUMPTION / ADJUSTMENT / SPOILAGE / RETURN entry."""
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.none(),
        label="Ingredient",
    )
    transaction_type = forms.ChoiceField(
        choices=InventoryTransaction.Type.choices,
        label="Transaction Type",
    )
    quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        label="Quantity",
    )
    direction = forms.ChoiceField(
        choices=[("IN", "In"), ("OUT", "Out")],
        label="Direction",
        required=False,
        initial="OUT",
    )
    unit_cost = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        label="Unit Cost (₱)",
    )
    reference = forms.CharField(
        max_length=MAX_REFERENCE_LENGTH,
        required=False,
        label="Reference",
    )
    reason = forms.CharField(
        max_length=MAX_REASON_LENGTH,
        required=False,
        label="Reason",
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["ingredient"].queryset = Ingredient.objects.filter(
            restaurant_id=restaurant_id,
            is_deleted=False,
        ).order_by("name")
        self._apply_classes()

    def clean_reason(self):
        value = self.cleaned_data.get("reason", "").strip()
        txn_type = self.cleaned_data.get("transaction_type")
        # FR-042: reason is mandatory for ADJUSTMENT, SPOILAGE, RETURN.
        if txn_type in {
            InventoryTransaction.Type.ADJUSTMENT,
            InventoryTransaction.Type.SPOILAGE,
            InventoryTransaction.Type.RETURN,
        } and not value:
            raise ValidationError("A reason is required for this transaction type.")
        return value

    def clean_unit_cost(self):
        value = self.cleaned_data.get("unit_cost")
        txn_type = self.cleaned_data.get("transaction_type")
        if txn_type == InventoryTransaction.Type.PURCHASE and value is None:
            raise ValidationError("Unit cost is required for a purchase.")
        if value is not None and value < 0:
            raise ValidationError("Unit cost cannot be negative.")
        return value

    def save(self):
        """Build (unsaved) InventoryTransaction with the signed quantity.
        Caller sets restaurant_id and user; the model computes the balance."""
        data = self.cleaned_data
        quantity = data["quantity"]
        txn_type = data["transaction_type"]
        if txn_type == InventoryTransaction.Type.ADJUSTMENT:
            if data["direction"] == "OUT":
                quantity = -quantity
        elif txn_type != InventoryTransaction.Type.PURCHASE:
            # CONSUMPTION / SPOILAGE / RETURN: always stock out.
            quantity = -quantity
        return InventoryTransaction(
            ingredient=data["ingredient"],
            transaction_type=txn_type,
            quantity=quantity,
            unit_cost=data["unit_cost"],
            reference=data["reference"].strip(),
            reason=data["reason"],
        )

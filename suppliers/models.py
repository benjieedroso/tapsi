from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Supplier(models.Model):
    """FR-050: Supplier master data. FR-053: suppliers with POs are
    deactivated (soft delete) rather than hard-deleted."""
    class PaymentTerms(models.TextChoices):
        COD = "COD", "Cash on Delivery"
        DAYS_7 = "7D", "7 Days"
        DAYS_15 = "15D", "15 Days"
        DAYS_30 = "30D", "30 Days"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=120)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(
        max_length=8,
        choices=PaymentTerms.choices,
        default=PaymentTerms.COD,
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "is_active", "deleted_at"])

    @property
    def has_purchase_orders(self):
        return self.purchase_orders.exists()

    @property
    def outstanding_balance(self):
        """FR-051: received but unpaid PO totals minus recorded payments."""
        from django.db.models import Sum
        from .models import PurchaseOrder

        received = Decimal("0")
        for po in self.purchase_orders.filter(
            status__in=[PurchaseOrder.Status.PARTIALLY_RECEIVED, PurchaseOrder.Status.RECEIVED]
        ):
            received += po.received_total
        paid = self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return max(received - paid, Decimal("0"))


class PurchaseOrder(models.Model):
    """FR-060..FR-065: purchase orders with line items, status flow,
    per-line partial receiving, and a sequential PO number."""
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ORDERED = "ORDERED", "Ordered"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
        RECEIVED = "RECEIVED", "Received"
        CANCELLED = "CANCELLED", "Cancelled"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    po_number = models.CharField(max_length=30, blank=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    placed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders_placed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("restaurant_id", "po_number")

    def __str__(self):
        return self.po_number or f"PO #{self.pk}"

    @property
    def total(self):
        """Derived: Σ line qty_ordered × unit_cost (BR-011 style)."""
        return sum((i.qty_ordered * i.unit_cost for i in self.items.all()), Decimal("0"))

    @property
    def received_total(self):
        """Σ line qty_received × unit_cost — drives supplier balances (FR-051)."""
        return sum((i.qty_received * i.unit_cost for i in self.items.all()), Decimal("0"))

    @property
    def is_read_only(self):
        return self.status == self.Status.RECEIVED

    def assign_po_number(self):
        """FR-063: sequential per restaurant: PO-2026-00042."""
        year = self.created_at.year if self.created_at else 2026
        seq = PurchaseOrder.objects.filter(
            restaurant_id=self.restaurant_id,
            po_number__startswith=f"PO-{year}-",
        ).count() + 1
        self.po_number = f"PO-{year}-{seq:05d}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.assign_po_number()
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    """FR-060/FR-062/FR-065: line items with ordered vs received quantities."""
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )
    ingredient = models.ForeignKey(
        "inventory.Ingredient",
        on_delete=models.PROTECT,
        related_name="po_items",
    )
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0.001)])
    qty_received = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=4, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.ingredient} × {self.qty_ordered}"

    @property
    def outstanding_qty(self):
        return self.qty_ordered - self.qty_received

    @property
    def line_total(self):
        return self.qty_ordered * self.unit_cost

    def save(self, *args, **kwargs):
        if self.qty_received > self.qty_ordered:
            raise ValidationError(
                f"Received quantity for \"{self.ingredient.name}\" exceeds ordered quantity."
            )
        super().save(*args, **kwargs)


class SupplierPayment(models.Model):
    """FR-052: payments against a supplier's received POs, reducing the
    outstanding balance."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_date = models.DateField()
    method = models.CharField(max_length=20, default="CASH")
    reference_no = models.CharField(max_length=60, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-payment_date", "-id")

    def __str__(self):
        return f"{self.supplier}: ₱{self.amount}"

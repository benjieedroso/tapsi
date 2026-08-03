from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

TWO_PLACES = Decimal("0.01")
HALF_UP = Decimal("0.005")


def round_money(value):
    return Decimal(value).quantize(TWO_PLACES, rounding="ROUND_HALF_UP")


def business_date_today():
    """BR-014: business day = creation date in Asia/Manila."""
    return timezone.localdate()


def generate_order_number(restaurant_id, business_date):
    """FR-081: per-restaurant, per-day sequential order number (#0042)."""
    seq = Order.objects.filter(
        restaurant_id=restaurant_id,
        business_date=business_date,
    ).count() + 1
    return f"#{seq:04d}"


class DiningTable(models.Model):
    """FR-090..FR-095: physical tables with status tracking."""
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        OCCUPIED = "OCCUPIED", "Occupied"
        RESERVED = "RESERVED", "Reserved"
        CLEANING = "CLEANING", "Cleaning"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=40)
    seating_capacity = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("restaurant_id", "name")

    def __str__(self):
        return self.name

    @property
    def open_orders(self):
        return self.orders.filter(
            status__in=[Order.Status.PENDING, Order.Status.PREPARING, Order.Status.READY]
        )

    @property
    def running_bill(self):
        """FR-095: sum of totals of open orders on this table."""
        return sum((o.total for o in self.open_orders), Decimal("0"))

    def set_status(self, status, user, reason=""):
        """FR-091: status changes recorded with user and timestamp."""
        if status not in DiningTable.Status.values:
            raise ValidationError("Invalid table status.")
        TableStatusLog.objects.create(
            restaurant_id=self.restaurant_id,
            table=self,
            old_status=self.status,
            new_status=status,
            changed_by=user,
            reason=reason,
        )
        self.status = status
        self.save(update_fields=["status", "updated_at"])


class TableStatusLog(models.Model):
    """FR-091: table status change trail."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    table = models.ForeignKey(DiningTable, on_delete=models.CASCADE, related_name="status_logs")
    old_status = models.CharField(max_length=12)
    new_status = models.CharField(max_length=12)
    changed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class Order(models.Model):
    """FR-080..FR-089: the core selling workflow."""
    class Type(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine-in"
        TAKE_OUT = "TAKE_OUT", "Take-out"
        DELIVERY = "DELIVERY", "Delivery"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class DiscountType(models.TextChoices):
        SENIOR = "SENIOR", "Senior Citizen (20%)"
        PWD = "PWD", "PWD (20%)"
        MANUAL = "MANUAL", "Manual"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    order_number = models.CharField(max_length=12, blank=True)  # #0042 (FR-081)
    reference = models.CharField(max_length=16, unique=True)    # global unique ref (FR-081)
    order_type = models.CharField(max_length=10, choices=Type.choices, default=Type.DINE_IN)
    table = models.ForeignKey(
        DiningTable, on_delete=models.PROTECT, null=True, blank=True,
        related_name="orders",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    business_date = models.DateField(default=business_date_today, db_index=True)  # BR-014

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_type = models.CharField(
        max_length=12, choices=DiscountType.choices, null=True, blank=True
    )
    discount_ref = models.CharField(max_length=40, blank=True)   # Senior/PWD ID number
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_discount_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_needs_approval = models.BooleanField(default=False)
    discount_approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="discounts_approved",
    )

    vatable_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_exempt_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    customer_name = models.CharField(max_length=120, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_address = models.TextField(blank=True)

    cancel_reason = models.CharField(max_length=255, blank=True)
    cancelled_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="orders_cancelled",
    )

    receipt_no = models.PositiveBigIntegerField(null=True, blank=True)  # FR-103 serial
    receipt_reprinted_count = models.PositiveSmallIntegerField(default=0)  # FR-104

    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="orders_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            import uuid
            self.reference = uuid.uuid4().hex[:16]
        super().save(*args, **kwargs)

    # ── Money math (BR-010, BR-011) ─────────────────────────────────

    @property
    def paid_amount(self):
        return sum(
            (p.amount for p in self.payments.all() if p.amount > 0), Decimal("0")
        )

    @property
    def refunded_amount(self):
        return abs(sum((p.amount for p in self.payments.all() if p.amount < 0), Decimal("0")))

    @property
    def outstanding_balance(self):
        return self.total - self.paid_amount

    @property
    def is_settled(self):
        return self.outstanding_balance <= Decimal("0")

    @property
    def elapsed_minutes(self):
        """FR-089: elapsed time since creation, for the kitchen queue."""
        return int((timezone.now() - self.created_at).total_seconds() // 60)

    def recompute_totals(self, user=None):
        """BR-011: subtotal = Σ(line qty × unit price + add-ons);
        discount/VAT math per FR-087/FR-103."""
        subtotal = sum(
            (line.line_total for line in self.items.all()), Decimal("0")
        )
        self.subtotal = round_money(subtotal)

        discount_amount = Decimal("0")
        if self.discount_type in {self.DiscountType.SENIOR, self.DiscountType.PWD}:
            discount_amount = round_money(subtotal * Decimal("0.20"))
        elif self.discount_type == self.DiscountType.MANUAL and self.manual_discount_pct:
            pct = self.manual_discount_pct
            discount_amount = round_money(subtotal * pct / Decimal("100"))

        self.discount_amount = round_money(discount_amount)

        # BR-009: Senior/PWD discounts are VAT-exempt.
        exempt = (
            discount_amount
            if self.discount_type in {self.DiscountType.SENIOR, self.DiscountType.PWD}
            else Decimal("0")
        )
        manual = (
            discount_amount
            if self.discount_type == self.DiscountType.MANUAL
            else Decimal("0")
        )
        vatable = subtotal - exempt - manual
        vat = round_money(vatable * Decimal("0.12"))

        self.vat_exempt_sales = round_money(exempt)
        self.vatable_sales = round_money(vatable)
        self.vat_amount = vat
        self.total = round_money(subtotal - discount_amount)
        self.save(
            update_fields=[
                "subtotal", "discount_amount", "vatable_sales",
                "vat_exempt_sales", "vat_amount", "total",
            ]
        )

    def apply_discount(self, discount_type, discount_ref="", pct=None, user=None):
        """FR-087: Senior/PWD 20% + ID capture; manual with >10% approval."""
        if self.status != self.Status.PENDING:
            raise ValidationError("Discounts can only be applied to PENDING orders.")
        if discount_type in {self.DiscountType.SENIOR, self.DiscountType.PWD}:
            if not discount_ref.strip():
                raise ValidationError("The discount ID number is required (RA 9994 / RA 10754).")
            self.discount_type = discount_type
            self.discount_ref = discount_ref.strip()
            self.manual_discount_pct = None
            self.discount_needs_approval = False
            self.discount_approved_by = None
        elif discount_type == self.DiscountType.MANUAL:
            if pct is None:
                raise ValidationError("A percentage is required for manual discounts.")
            if pct <= 0 or pct > 100:
                raise ValidationError("Manual discount percentage must be between 0 and 100.")
            from accounts.models import User
            self.discount_type = self.DiscountType.MANUAL
            self.discount_ref = discount_ref.strip()
            self.manual_discount_pct = pct
            is_manager = user is not None and user.role in {User.Role.OWNER, User.Role.MANAGER}
            self.discount_needs_approval = pct > 10 and not is_manager
            self.discount_approved_by = user if is_manager and pct > 10 else None
        else:
            raise ValidationError("Invalid discount type.")
        self.recompute_totals()

    def approve_discount(self, user):
        """Manager/Owner approval for manual discounts above 10%."""
        if not self.discount_needs_approval:
            raise ValidationError("This discount does not require approval.")
        from accounts.models import User
        if user.role not in {User.Role.OWNER, User.Role.MANAGER}:
            raise ValidationError("Only Owner/Manager can approve discounts.")
        self.discount_needs_approval = False
        self.discount_approved_by = user
        self.save(update_fields=["discount_needs_approval", "discount_approved_by"])

    # ── Status flow (FR-083, FR-084, FR-085) ────────────────────────

    def transition_to(self, status, user, reason=""):
        allowed = {
            self.Status.PENDING: {
                self.Status.PREPARING, self.Status.READY,
                self.Status.COMPLETED, self.Status.CANCELLED,
            },
            self.Status.PREPARING: {self.Status.READY, self.Status.CANCELLED},
            self.Status.READY: {self.Status.COMPLETED, self.Status.CANCELLED},
        }.get(self.status, set())
        if status not in allowed:
            raise ValidationError(
                f"Cannot move an order from {self.get_status_display()} to {Order.Status(status).label}."
            )
        OrderStatusHistory.objects.create(
            restaurant_id=self.restaurant_id,
            order=self,
            old_status=self.status,
            new_status=status,
            changed_by=user,
            reason=reason,
        )
        self.status = status
        self.save(update_fields=["status", "updated_at"])

    # ── Completion (FR-085, FR-072, FR-073) ─────────────────────────

    def complete(self, user, notify_service=None):
        """Verify payment, deduct stock via recipes, complete atomically."""
        from .services import settle_order

        return settle_order(self, user, notify_service=notify_service)

    def cancel(self, user, reason):
        """FR-086/BR-003: require reason; restore consumed inventory."""
        from .services import cancel_order

        return cancel_order(self, user, reason)


class OrderItem(models.Model):
    """FR-082: line with snapshot of name/price (BR-007)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        "menu.MenuItem", on_delete=models.PROTECT, null=True, related_name="order_items"
    )
    item_name = models.CharField(max_length=120)          # snapshot at sale
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)  # snapshot at sale
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    notes = models.CharField(max_length=255, blank=True)  # e.g., "no onions"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.item_name} × {self.quantity}"

    @property
    def addons_total(self):
        return sum((a.price for a in self.addons.all()), Decimal("0"))

    @property
    def line_total(self):
        return round_money((self.unit_price + self.addons_total) * self.quantity)


class OrderItemAddon(models.Model):
    """FR-082: add-on snapshot per order item."""
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="addons")
    addon = models.ForeignKey("menu.AddOn", on_delete=models.PROTECT, null=True)
    addon_name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.addon_name


class OrderStatusHistory(models.Model):
    """FR-089: timestamped status changes."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=12, choices=Order.Status.choices)
    new_status = models.CharField(max_length=12, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class Payment(models.Model):
    """FR-100..FR-105: append-only settlement records (BR-005)."""
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        GCASH = "GCASH", "GCash"
        CARD = "CARD", "Card"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=14, choices=Method.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # negative = refund
    tendered = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    change_given = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reference_no = models.CharField(max_length=60, blank=True)
    refund_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds"
    )
    refund_reason = models.CharField(max_length=255, blank=True)
    received_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    business_date = models.DateField(default=business_date_today, db_index=True)  # BR-014
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_method_display()} {self.amount} ({self.order})"

    def delete(self, *args, **kwargs):
        raise ValidationError("Payments are immutable; refund with a negative payment.")

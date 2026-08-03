from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Ingredient(models.Model):
    """FR-040: Ingredient master data — name, unit of measure, minimum stock,
    average unit cost, default supplier.

    FR-041: Current stock is NOT stored — it is derived from the sum of
    inventory transactions (see InventoryTransaction.resulting_balance).
    """
    class UnitOfMeasure(models.TextChoices):
        GRAM = "g", "Gram (g)"
        KILOGRAM = "kg", "Kilogram (kg)"
        MILLILITER = "ml", "Milliliter (ml)"
        LITER = "L", "Liter (L)"
        PIECE = "pc", "Piece (pc)"
        PACK = "pack", "Pack"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=100)
    unit_of_measure = models.CharField(
        max_length=10,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.PIECE,
    )
    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    # FR-047: maintained as weighted average cost; recalculated on PURCHASE.
    average_unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    # Supplier module (Module 6) not built yet — keep as plain id like restaurant_id.
    default_supplier_id = models.PositiveIntegerField(null=True, blank=True)
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
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    @property
    def current_stock(self):
        """FR-041: Derived from the last ledger entry's resulting balance."""
        balance = self.transactions.order_by("-id").values_list(
            "resulting_balance", flat=True
        ).first()
        return balance if balance is not None else 0

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock


class InventoryTransaction(models.Model):
    """FR-042/FR-043: Immutable stock ledger. Every transaction records the
    ingredient, type, signed quantity, unit cost (where applicable), resulting
    balance, reference, user, and timestamp. Corrections are compensating
    entries — deletion is forbidden (FR-043)."""
    class Type(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        CONSUMPTION = "CONSUMPTION", "Consumption"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        SPOILAGE = "SPOILAGE", "Spoilage"
        RETURN = "RETURN", "Return"

    # Fixed sign of each type (+in / -out); ADJUSTMENT may be either.
    SIGN = {
        Type.PURCHASE: 1,
        Type.CONSUMPTION: -1,
        Type.ADJUSTMENT: None,
        Type.SPOILAGE: -1,
        Type.RETURN: -1,
    }

    restaurant_id = models.PositiveIntegerField(db_index=True)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=12, choices=Type.choices)
    # Signed quantity: positive = stock in, negative = stock out (FR-043).
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    resulting_balance = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    reason = models.CharField(max_length=500, blank=True)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return f"{self.ingredient}: {self.quantity} ({self.transaction_type})"

    def _normalized_quantity(self):
        sign = self.SIGN[self.transaction_type]
        if sign is not None and (sign * self.quantity) < 0:
            return -self.quantity
        return self.quantity

    def save(self, *args, **kwargs):
        from decimal import Decimal

        self.quantity = Decimal(self.quantity)
        self.quantity = self._normalized_quantity()
        self.restaurant_id = self.ingredient.restaurant_id

        previous = (
            self.ingredient.transactions.order_by("-id")
            .values_list("resulting_balance", flat=True)
            .first()
        )
        prev_balance = Decimal(previous) if previous is not None else Decimal("0")
        new_balance = prev_balance + self.quantity

        # FR-044: reject transactions that would make stock negative.
        if new_balance < 0:
            raise ValidationError(
                f"Insufficient stock for \"{self.ingredient.name}\": "
                f"balance would be {new_balance} "
                f"(available: {prev_balance}, transaction: {self.quantity})."
            )

        self.resulting_balance = new_balance

        super().save(*args, **kwargs)

        # FR-047: weighted average unit cost on PURCHASE.
        if (
            self.transaction_type == self.Type.PURCHASE
            and self.unit_cost is not None
            and self.quantity > 0
        ):
            ingredient = self.ingredient
            old_avg = ingredient.average_unit_cost
            old_qty = prev_balance
            new_qty = new_balance
            if old_qty > 0:
                new_avg = (old_avg * old_qty + self.unit_cost * self.quantity) / new_qty
            else:
                new_avg = self.unit_cost
            ingredient.average_unit_cost = Decimal(new_avg)
            ingredient.save(update_fields=["average_unit_cost"])

        # FR-045: reconcile low-stock notifications (once per ingredient
        # until replenished above the minimum threshold).
        LowStockAlert.reconcile(self.ingredient)

    def delete(self, *args, **kwargs):
        # FR-043: transactions are immutable — corrections are compensating entries.
        raise ValidationError(
            "Inventory transactions are immutable; corrections require a "
            "compensating entry, not deletion."
        )


class LowStockAlert(models.Model):
    """FR-045: Created once per ingredient when stock falls to or below the
    minimum, and resolved once stock is replenished above the threshold."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="low_stock_alerts",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-opened_at",)

    def __str__(self):
        return f"{self.ingredient} low stock alert"

    @classmethod
    def reconcile(cls, ingredient):
        """Open an alert when at/below minimum; close when back above it."""
        from django.utils import timezone

        open_alerts = cls.objects.filter(
            ingredient=ingredient,
            resolved_at__isnull=True,
        )
        if ingredient.current_stock <= ingredient.minimum_stock:
            if not open_alerts.exists():
                cls.objects.create(
                    restaurant_id=ingredient.restaurant_id,
                    ingredient=ingredient,
                )
        else:
            open_alerts.update(resolved_at=timezone.now())

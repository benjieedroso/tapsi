from django.db import models
from django.utils import timezone


class DailyClosing(models.Model):
    """FR-140..FR-145: end-of-day cash reconciliation and day locking
    (BR-008). One closing per business day."""
    class Status(models.TextChoices):
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    business_date = models.DateField(db_index=True)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    counted_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance_note = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CLOSED)
    closed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="days_closed",
    )
    reopened_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="days_reopened",
    )
    reopen_reason = models.CharField(max_length=255, blank=True)
    reopened_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("restaurant_id", "business_date")
        ordering = ("-business_date",)

    def __str__(self):
        return f"{self.business_date}: {self.get_status_display()}"

    @classmethod
    def is_locked(cls, restaurant_id, business_date):
        """BR-008: closed days reject new orders/payments/expenses."""
        return cls.objects.filter(
            restaurant_id=restaurant_id,
            business_date=business_date,
            status=cls.Status.CLOSED,
        ).exists()

    @classmethod
    def current_float(cls, restaurant_id):
        """FR-145: opening float defaults to the previous closing's float."""
        previous = cls.objects.filter(
            restaurant_id=restaurant_id,
        ).order_by("-business_date").first()
        return previous.counted_cash if previous else 0

    @classmethod
    def expected_cash_for(cls, restaurant_id, business_date):
        """FR-140: expected cash = opening float + cash sales − cash refunds
        − cash expenses."""
        from decimal import Decimal

        from expenses.models import Expense
        from orders.models import Payment

        opening = cls.current_float(restaurant_id)
        cash_sales = sum(
            (p.amount for p in Payment.objects.filter(
                restaurant_id=restaurant_id,
                business_date=business_date,
                method=Payment.Method.CASH,
                amount__gt=0,
            )),
            Decimal("0"),
        )
        cash_refunds = abs(sum(
            (p.amount for p in Payment.objects.filter(
                restaurant_id=restaurant_id,
                business_date=business_date,
                method=Payment.Method.CASH,
                amount__lt=0,
            )),
            Decimal("0"),
        ))
        cash_expenses = sum(
            (e.amount for e in Expense.objects.filter(
                restaurant_id=restaurant_id,
                expense_date=business_date,
                payment_method="CASH",
                status="APPROVED",
            )),
            Decimal("0"),
        )
        return opening + cash_sales - cash_refunds - cash_expenses

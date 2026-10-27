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
        """FR-140: expected cash = opening float + cash sales − cash refunds − cash expenses."""
        from decimal import Decimal
        from datetime import datetime, date
        from django.db.models import Sum

        from expenses.models import Expense
        from orders.models import Payment

        # 1. Parse string date to a date object if necessary
        if isinstance(business_date, str):
            business_date = datetime.strptime(business_date, "%Y-%m-%d").date()

        opening = cls.current_float(restaurant_id)

        # 2. Query positive cash payments (Sales)
        sales_agg = Payment.objects.filter(
            restaurant_id=restaurant_id,
            business_date=business_date,
            method=Payment.Method.CASH,
            amount__gt=0,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # 3. Query negative cash payments (Refunds)
        refunds_agg = Payment.objects.filter(
            restaurant_id=restaurant_id,
            business_date=business_date,
            method=Payment.Method.CASH,
            amount__lt=0,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        cash_refunds = abs(refunds_agg)

        # 4. Query approved cash expenses
        expenses_agg = Expense.objects.filter(
            restaurant_id=restaurant_id,
            expense_date=business_date,
            payment_method="CASH",
            status="APPROVED",
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        return opening + sales_agg - cash_refunds - expenses_agg

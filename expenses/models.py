from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def business_date_today():
    return timezone.localdate()


class Expense(models.Model):
    """FR-110..FR-113: operating expenses with approval workflow and
    business-day locking (BR-008)."""
    class Category(models.TextChoices):
        ELECTRICITY = "Electricity", "Electricity"
        WATER = "Water", "Water"
        INTERNET = "Internet", "Internet"
        RENT = "Rent", "Rent"
        SALARY = "Salary", "Salary"
        SUPPLIES = "Supplies", "Supplies"
        MAINTENANCE = "Maintenance", "Maintenance"
        GAS_LPG = "Gas/LPG", "Gas/LPG"
        TRANSPORTATION = "Transportation", "Transportation"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    expense_date = models.DateField(default=business_date_today, db_index=True)
    payee = models.CharField(max_length=120, blank=True)
    payment_method = models.CharField(max_length=20, default="CASH")
    notes = models.TextField(blank=True)
    receipt_image = models.ImageField(upload_to="expense_receipts/", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.APPROVED)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expenses_created",
    )
    approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expenses_approved",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-expense_date", "-created_at")

    def __str__(self):
        return f"{self.category}: ₱{self.amount} ({self.expense_date})"

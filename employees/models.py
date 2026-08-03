from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Employee(models.Model):
    """FR-120..FR-123: staff records and attendance. Salary info is
    Owner/Manager-visible only (FR-121)."""
    class EmploymentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    restaurant_id = models.PositiveIntegerField(db_index=True)
    full_name = models.CharField(max_length=120)
    nickname = models.CharField(max_length=60, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=80, blank=True)
    employment_status = models.CharField(
        max_length=10,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )
    date_hired = models.DateField(null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("full_name",)

    def __str__(self):
        return self.full_name

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


class Attendance(models.Model):
    """FR-122: clock-in/out per employee per day; edits audit-logged."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    work_date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("employee", "work_date")
        ordering = ("-work_date",)

    def __str__(self):
        return f"{self.employee} {self.work_date}"

    @property
    def hours(self):
        """FR-123: total hours for the day."""
        if not (self.clock_in and self.clock_out):
            return 0
        if self.clock_out <= self.clock_in:
            return 0
        return round((self.clock_out - self.clock_in).total_seconds() / 3600, 2)

    def clean(self):
        if self.clock_in and self.clock_out and self.clock_out < self.clock_in:
            raise ValidationError("Clock-out cannot be before clock-in.")

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    """FR-030: Category CRUD — name, display order, active flag.

    Category names are unique per restaurant.
    """
    restaurant_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=80)
    display_order = models.SmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("display_order", "name")
        unique_together = ("restaurant_id", "name")

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """FR-031: Menu Item CRUD — name, description, category, price,
    availability, prep time, image.  FR-035: Soft delete."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    prep_minutes = models.SmallIntegerField(default=10)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to="menu_images/", blank=True)
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

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = MenuItem.objects.get(pk=self.pk)
                if old.price != self.price:
                    from .models import MenuItemPriceHistory  # noqa: avoid self-import at module level
                    MenuItemPriceHistory.objects.create(
                        menu_item=self,
                        old_price=old.price,
                        new_price=self.price,
                    )
            except MenuItem.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class MenuItemPriceHistory(models.Model):
    """FR-036: Price change history — old price, new price, changed by, timestamp."""
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="price_history",
    )
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    changed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.menu_item}: ₱{self.old_price} → ₱{self.new_price}"


class AddOn(models.Model):
    """FR-033: Add-ons — name, price, optional recipe, attachable to menu items."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=80)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class MenuItemAddOn(models.Model):
    """Many-to-many link between MenuItem and AddOn (FR-033)."""
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="addon_links",
    )
    addon = models.ForeignKey(
        AddOn,
        on_delete=models.CASCADE,
        related_name="menu_item_links",
    )

    class Meta:
        unique_together = ("menu_item", "addon")

    def __str__(self):
        return f"{self.menu_item} + {self.addon}"

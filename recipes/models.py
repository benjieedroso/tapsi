from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Recipe(models.Model):
    """FR-070: one recipe per menu item (or add-on), consisting of
    ingredient lines. FR-075: changes never touch historical consumption."""
    restaurant_id = models.PositiveIntegerField(db_index=True)
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recipes",
    )
    addon = models.ForeignKey(
        "menu.AddOn",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recipes",
    )
    name = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return self.name or f"Recipe #{self.pk}"

    @property
    def target(self):
        return self.menu_item or self.addon

    @property
    def cost(self):
        """FR-071: recipe cost from ingredient weighted average costs."""
        return sum(
            (line.ingredient.average_unit_cost * line.quantity for line in self.lines.all()),
            Decimal("0"),
        )

    @property
    def margin(self):
        """FR-071: margin against the selling price."""
        target = self.target
        if not target:
            return None
        price = Decimal(target.price)
        if price <= 0:
            return None
        return ((price - self.cost) / price) * Decimal("100")

    @classmethod
    def get_for(cls, menu_item=None, addon=None):
        if menu_item is not None:
            return cls.objects.filter(menu_item=menu_item).first()
        if addon is not None:
            return cls.objects.filter(addon=addon).first()
        return None


class RecipeIngredient(models.Model):
    """FR-070: ingredient line — ingredient, quantity (in ingredient's unit)."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    ingredient = models.ForeignKey(
        "inventory.Ingredient",
        on_delete=models.PROTECT,
        related_name="recipe_lines",
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
    )

    class Meta:
        unique_together = ("recipe", "ingredient")
        ordering = ("id",)

    def __str__(self):
        return f"{self.ingredient.name} × {self.quantity}"

    @property
    def line_cost(self):
        return self.ingredient.average_unit_cost * self.quantity

    def save(self, *args, **kwargs):
        if self.ingredient.restaurant_id != self.recipe.restaurant_id:
            raise ValidationError("Recipe ingredients must belong to the same restaurant.")
        super().save(*args, **kwargs)

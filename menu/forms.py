from django import forms
from django.core.exceptions import ValidationError

from .models import AddOn, Category, MenuItem

MAX_CATEGORY_NAME = 80
MAX_ITEM_NAME = 120
MAX_DESCRIPTION_LENGTH = 1000


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "display_order", "is_active")
        labels = {
            "display_order": "Display Order",
            "is_active": "Active",
        }
        widgets = {
            "display_order": forms.NumberInput(attrs={"style": "max-width: 100px;"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Category name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Category name must be at least 2 characters.")
        if len(value.strip()) > MAX_CATEGORY_NAME:
            raise ValidationError(f"Category name must be {MAX_CATEGORY_NAME} characters or fewer.")
        # Unique per restaurant
        qs = Category.objects.filter(
            restaurant_id=self.restaurant_id,
            name__iexact=value.strip(),
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A category with this name already exists.")
        return value.strip()

    def clean_display_order(self):
        value = self.cleaned_data.get("display_order", 0)
        if value < 0:
            raise ValidationError("Display order cannot be negative.")
        return value


def validate_menu_image(upload):
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError("Menu images must be 5 MB or smaller.")
    if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")


class MenuItemForm(StyledFormMixin, forms.ModelForm):
    image = forms.FileField(required=False, validators=[validate_menu_image])

    class Meta:
        model = MenuItem
        fields = ("name", "description", "category", "price", "prep_minutes", "is_available", "image")
        labels = {
            "prep_minutes": "Prep Time (minutes)",
            "is_available": "Available",
        }
        widgets = {
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "prep_minutes": forms.NumberInput(attrs={"min": "1", "style": "max-width: 100px;"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            restaurant_id=restaurant_id,
        ).order_by("display_order", "name")
        self.fields["category"].empty_label = "— No category —"
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Menu item name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Menu item name must be at least 2 characters.")
        if len(value.strip()) > MAX_ITEM_NAME:
            raise ValidationError(f"Menu item name must be {MAX_ITEM_NAME} characters or fewer.")
        return value.strip()

    def clean_description(self):
        value = self.cleaned_data.get("description", "").strip()
        if len(value) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.")
        return value

    def clean_price(self):
        value = self.cleaned_data.get("price")
        if value is None:
            raise ValidationError("Price is required.")
        if value < 0:
            raise ValidationError("Price cannot be negative.")
        return value

    def clean_prep_minutes(self):
        value = self.cleaned_data.get("prep_minutes", 10)
        if value < 1:
            raise ValidationError("Preparation time must be at least 1 minute.")
        if value > 999:
            raise ValidationError("Preparation time cannot exceed 999 minutes.")
        return value


class AddOnForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AddOn
        fields = ("name", "price", "is_available")
        labels = {
            "is_available": "Available",
        }
        widgets = {
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, restaurant_id=None, **kwargs):
        self.restaurant_id = restaurant_id
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Add-on name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Add-on name must be at least 2 characters.")
        if len(value.strip()) > MAX_CATEGORY_NAME:
            raise ValidationError(f"Add-on name must be {MAX_CATEGORY_NAME} characters or fewer.")
        return value.strip()

    def clean_price(self):
        value = self.cleaned_data.get("price")
        if value is None:
            raise ValidationError("Price is required.")
        if value < 0:
            raise ValidationError("Price cannot be negative.")
        return value

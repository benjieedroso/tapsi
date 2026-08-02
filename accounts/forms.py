from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Restaurant, User
from .validators import validate_name, validate_phone, validate_tin

MAX_NAME_LENGTH = 150
MAX_ADDRESS_LENGTH = 500


class StyledFormMixin:
    def _apply_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class RegistrationForm(StyledFormMixin, forms.Form):
    restaurant_name = forms.CharField(max_length=150, label="Restaurant name")
    first_name = forms.CharField(max_length=150, label="Your first name")
    last_name = forms.CharField(max_length=150, label="Your last name", required=False)
    email = forms.EmailField()
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_restaurant_name(self):
        value = self.cleaned_data["restaurant_name"]
        if not value or not value.strip():
            raise ValidationError("Restaurant name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Restaurant name must be at least 2 characters.")
        return value.strip()

    def clean_first_name(self):
        value = self.cleaned_data["first_name"]
        if not value or not value.strip():
            raise ValidationError("First name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        return value.strip()

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "")
        if value and len(value.strip()) < 2:
            raise ValidationError("Last name must be at least 2 characters.")
        return value.strip()

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account already uses this email address.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")
        if password1:
            candidate = User(email=cleaned.get("email", ""), first_name=cleaned.get("first_name", ""))
            try:
                password_validation.validate_password(password1, candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    @transaction.atomic
    def save(self):
        restaurant = Restaurant.objects.create(name=self.cleaned_data["restaurant_name"])
        return User.objects.create_user(
            email=self.cleaned_data["email"], password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"], last_name=self.cleaned_data["last_name"],
            restaurant=restaurant, role=User.Role.OWNER,
        )


class EmailAuthenticationForm(StyledFormMixin, forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email", "").lower()
        password = cleaned.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise ValidationError("Unable to log in with the provided credentials.")
        return cleaned

    def get_user(self):
        return self.user_cache


class StaffUserForm(StyledFormMixin, forms.ModelForm):
    temporary_password = forms.CharField(widget=forms.PasswordInput, help_text="The staff member must change this on first login.")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "role")

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        if actor.role == User.Role.MANAGER:
            self.fields["role"].choices = [(User.Role.CASHIER, "Cashier"), (User.Role.KITCHEN, "Kitchen")]
        self._apply_classes()

    def clean_first_name(self):
        value = self.cleaned_data.get("first_name", "")
        if not value or not value.strip():
            raise ValidationError("First name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        return value.strip()

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "")
        if value and len(value.strip()) < 2:
            raise ValidationError("Last name must be at least 2 characters.")
        return value.strip()

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "")
        if value:
            value = value.strip()
            validate_phone(value)
        return value

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account already uses this email address.")
        return email

    def clean_temporary_password(self):
        password = self.cleaned_data["temporary_password"]
        password_validation.validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        # ``username`` remains a unique database column inherited from
        # AbstractUser, even though TAPSI authenticates exclusively by email.
        # Keep it in sync so ModelForm-created staff accounts do not attempt
        # to store the duplicate empty-string default.
        user.username = user.email
        user.restaurant = self.actor.restaurant
        user.must_change_password = True
        user.set_password(self.cleaned_data["temporary_password"])
        if commit:
            user.save()
        return user


class FirstPasswordChangeForm(StyledFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()


class CurrentPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()


def validate_avatar(upload):
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError("Avatar files must be 5 MB or smaller.")
    if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")


class ProfileForm(StyledFormMixin, forms.ModelForm):
    avatar = forms.FileField(required=False, validators=[validate_avatar])

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "avatar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_first_name(self):
        value = self.cleaned_data.get("first_name", "")
        if not value or not value.strip():
            raise ValidationError("First name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        return value.strip()

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "")
        if value and len(value.strip()) < 2:
            raise ValidationError("Last name must be at least 2 characters.")
        return value.strip()

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "")
        if value:
            value = value.strip()
            validate_phone(value)
        return value


class EmailChangeForm(StyledFormMixin, forms.Form):
    email = forms.EmailField(label="New email address")

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if email == self.user.email:
            raise ValidationError("This is already your email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account already uses this email address.")
        return email


class StaffEditForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_first_name(self):
        value = self.cleaned_data.get("first_name", "")
        if not value or not value.strip():
            raise ValidationError("First name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        return value.strip()

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "")
        if value and len(value.strip()) < 2:
            raise ValidationError("Last name must be at least 2 characters.")
        return value.strip()

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "")
        if value:
            value = value.strip()
            validate_phone(value)
        return value

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role == User.Role.OWNER:
            raise ValidationError("Cannot assign Owner role through edit. Use registration instead.")
        return role


class RestaurantSettingsForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ("name", "address", "contact_number", "tin", "receipt_footer", "is_vat_registered")
        labels = {
            "name": "Restaurant Name",
            "contact_number": "Contact Number",
            "receipt_footer": "Receipt Footer Message",
            "is_vat_registered": "VAT Registered",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        if not value or not value.strip():
            raise ValidationError("Restaurant name cannot be blank.")
        if len(value.strip()) < 2:
            raise ValidationError("Restaurant name must be at least 2 characters.")
        return value.strip()

    def clean_contact_number(self):
        value = self.cleaned_data.get("contact_number", "")
        if value:
            value = value.strip()
            validate_phone(value)
        return value

    def clean_tin(self):
        value = self.cleaned_data.get("tin", "")
        if value:
            value = value.strip()
            validate_tin(value)
        return value

    def clean_address(self):
        value = self.cleaned_data.get("address", "").strip()
        if len(value) > MAX_ADDRESS_LENGTH:
            raise ValidationError(f"Address must be {MAX_ADDRESS_LENGTH} characters or fewer.")
        return value

    def clean_receipt_footer(self):
        return self.cleaned_data.get("receipt_footer", "").strip()


class AdminPasswordResetForm(StyledFormMixin, forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, help_text="The staff member must change this on first login.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_classes()

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]
        password_validation.validate_password(password)
        return password

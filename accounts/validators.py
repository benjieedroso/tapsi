import re

from django.core.exceptions import ValidationError


class PasswordLetterAndNumberValidator:
    def validate(self, password, user=None):
        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            raise ValidationError("Your password must contain at least one letter and one number.")

    def get_help_text(self):
        return "Your password must contain at least one letter and one number."


PhoneNumberRegex = re.compile(r"^[\d+() -]+$")
TINRegex = re.compile(r"^\d{3}-\d{3}-\d{3}-\d{3}$")


def validate_phone(value):
    value = value.strip()
    if not value:
        return
    if not PhoneNumberRegex.match(value):
        raise ValidationError("Enter a valid phone number (e.g., 09171234567 or +63 917 123 4567).")
    digits = re.sub(r"\D", "", value)
    if digits.startswith("0") and len(digits) != 11:
        raise ValidationError("Local phone numbers must be 11 digits (e.g., 09171234567).")
    if digits.startswith("63") and len(digits) != 12:
        raise ValidationError("International phone numbers must be 12 digits (e.g., +639171234567).")
    if not digits.startswith("0") and not digits.startswith("63"):
        if len(digits) < 10 or len(digits) > 12:
            raise ValidationError("Phone number must be 10 to 12 digits.")


def validate_tin(value):
    value = value.strip()
    if not value:
        return
    if not TINRegex.match(value):
        raise ValidationError("Enter a valid TIN in the format XXX-XXX-XXX-XXX.")


def validate_name(value):
    if not value or not value.strip():
        raise ValidationError("This field cannot be blank.")
    if len(value.strip()) < 2:
        raise ValidationError("Must be at least 2 characters.")

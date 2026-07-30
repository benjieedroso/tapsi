from django.core.exceptions import ValidationError


class PasswordLetterAndNumberValidator:
    def validate(self, password, user=None):
        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            raise ValidationError("Your password must contain at least one letter and one number.")

    def get_help_text(self):
        return "Your password must contain at least one letter and one number."

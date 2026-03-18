from django.core.exceptions import ValidationError


def contains_only_letters_validator(value):
    if not value.isalpha():
        raise ValidationError('The name must contain only letters!')
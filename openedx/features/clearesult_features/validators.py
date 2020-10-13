"""
Validation utils for clearesult features app.
"""
from csv import Error

from django.core.exceptions import ValidationError


def validate_csv_extension(file):
    if not file.name.endswith('.csv'):
        raise ValidationError('Invalid file format. Only csv files are supported.')

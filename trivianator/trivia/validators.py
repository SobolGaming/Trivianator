import os

from django.core.exceptions import ValidationError

def json_file_validator(value):
    filename, ext = os.path.splitext(value.name)
    if str(ext) != '.json':
        raise ValidationError("Must be a JSON file")
    return True

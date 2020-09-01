import os

from django.core.exceptions import ValidationError

def archive_file_validator(value):
    filename, ext = os.path.splitext(value.name)
    if str(ext) != '.tgz':
        raise ValidationError("Must be a *.tgz file")
    return True

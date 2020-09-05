import os

from django.core.exceptions import ValidationError

def archive_file_validator(value):
    filename, ext = (value.name).split('.', 1)
    if str(ext) == 'tgz' or str(ext) == 'tar.gz' or str(ext) == 'tar':
        return True
    raise ValidationError("Must be a *.tgz, *.tar.gz, or *.tar file")

import csv
import os
import io

from django.core.exceptions import ValidationError

CREATE_USER_REQUIRED_HEADER  = ['username','email','password','first name','last name']

def csv_file_validator(value, model_type):
    filename, ext = os.path.splitext(value.name)
    if str(ext) != '.csv':
        raise ValidationError("Must be a csv file")
    decoded_file = value.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    reader = csv.reader(io_string, delimiter=';', quotechar='|')
    header_ = next(reader)[0].split(',')
    if header_[-1] == '':
        header_.pop()
    if model_type == 'CREATE_USER':
        required_header = CREATE_USER_REQUIRED_HEADER
        if required_header != header_:
            raise ValidationError("Invalid File. Please use valid CSV Header with Model Type and/or Staff Upload Template.")
    else:
        raise ValidationError("Invalid CSV File. Please use valid CSV Header and Model Type and/or Staff Upload Template.")
    return True
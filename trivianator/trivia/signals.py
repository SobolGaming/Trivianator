import django.dispatch

json_uploaded = django.dispatch.Signal(providing_args=["user", "json_file_list"])

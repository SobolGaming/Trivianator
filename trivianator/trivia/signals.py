import django.dispatch

archive_uploaded = django.dispatch.Signal(providing_args=["user", "archive_file_list"])

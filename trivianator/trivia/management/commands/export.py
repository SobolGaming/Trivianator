# The MIT License (MIT)
#
# Copyright (c) 2014 Nathan Osman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Taken mostly from https://github.com/nathan-osman/django-archive
from django.core.management.base import BaseCommand, CommandError

from datetime import datetime
from io import BytesIO
from json import dump
from os import path
from tarfile import TarInfo, TarFile

from django.apps.registry import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.encoding import smart_bytes

from ... import __version__

class MixedIO(BytesIO):
    """
    A BytesIO that accepts and encodes Unicode data.

    This class was born out of a need for a BytesIO that would accept writes of
    both bytes and Unicode data - allowing identical usage from both Python 2
    and Python 3.
    """

    def rewind(self):
        """
        Seeks to the beginning and returns the size.
        """
        size = self.tell()
        self.seek(0)
        return size

    def write(self, data):
        """
        Writes the provided data, converting Unicode to bytes as needed.
        """
        BytesIO.write(self, smart_bytes(data))

class Command(BaseCommand):
    """
    Create a compressed backup of the database tables and stored media.
    """
    help = 'Exports compressed copy of db tables and media.  Mostly for complete backup and reimport.  Will throw errors if the destination already has the same media file paths'

    def handle(self, *args, **kwargs):
        """
        Process the command.
        """
        tar = self._create_archive()
        self._dump_db(tar)
        self._dump_files(tar)
        self._dump_meta(tar)
        tar.close()
        self.stdout.write("Backup completed.")

    def _create_archive(self):
        """
        Create the archive and return the TarFile.
        """
        filename = getattr(settings, 'ARCHIVE_FILENAME', '%Y-%m-%d--%H-%M-%S')
        fmt = getattr(settings, 'ARCHIVE_FORMAT', 'bz2')
        absolute_path = path.join(
            getattr(settings, 'ARCHIVE_DIRECTORY', ''),
            '%s.tar.%s' % (datetime.today().strftime(filename), fmt)
        )
        return TarFile.open(absolute_path, 'w:%s' % fmt)

    def _dump_db(self, tar):
        """
        Dump the rows in each model to the archive.
        """

        # Determine the list of models to exclude
        exclude = getattr(settings, 'ARCHIVE_EXCLUDE', (
            'auth.Permission',
            'contenttypes.ContentType',
            'sessions.Session',
        ))

        # Dump the tables to a BytesIO
        data = MixedIO()
        call_command('dumpdata', all=True, format='json', exclude=exclude, stdout=data, natural_foreign=True)
        info = TarInfo('data.json')
        info.size = data.rewind()
        tar.addfile(info, data)

    def _dump_files(self, tar):
        """
        Dump all uploaded media to the archive.
        """

        # Loop through all models and find FileFields
        for model in apps.get_models():

            # Get the name of all file fields in the model
            field_names = []
            for field in model._meta.fields:
                if isinstance(field, models.FileField):
                    field_names.append(field.name)

            # If any were found, loop through each row
            if len(field_names):
                for row in model.objects.all():
                    for field_name in field_names:
                        field = getattr(row, field_name)
                        if field:
                            field.open()
                            info = TarInfo('mediafiles/'+field.name)
                            info.size = field.size
                            tar.addfile(info, field)
                            field.close()

    def _dump_meta(self, tar):
        """
        Dump metadata to the archive.
        """
        data = MixedIO()
        dump({'version': __version__}, data)
        info = TarInfo('meta.json')
        info.size = data.rewind()
        tar.addfile(info, data)

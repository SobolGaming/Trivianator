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

import json
from tarfile import TarInfo, TarFile
import tempfile
from pathlib import Path
import shutil
import os


from django.apps.registry import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.encoding import smart_bytes

from ... import __version__

class Command(BaseCommand):
    """
    Create a compressed backup of the database tables and stored media.
    """
    help = 'Imports compressed copy of db tables and media. Mostly for complete backup and reimport.  Will throw errors if the destination already has the same media file paths'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('data_tarfile', nargs='+', type=str)

    def handle(self, *args, **kwargs):
        """
        Process the command.
        """
        data_files = kwargs['data_tarfile']

        for data_file in data_files:
            with tempfile.TemporaryDirectory() as tmpdir:
                tdir = Path(tmpdir)
                if self._check_and_extract_archive(tdir,data_file):
                    self._import_files(tdir)
                    self._import_db(tdir)
                    self.stdout.write(self.style.SUCCESS("Import completed."))
                else:
                    self.stdout.write(self.style.ERROR("Import failed."))

    def _check_and_extract_archive(self,tmpdir,data_file):
        """
        Create the archive and return the TarFile.
        """

        tar = TarFile.open(data_file, 'r:*')
        if self._check_meta(tar,tmpdir):
            tar.extractall(str(tmpdir))
            tar.close()
            return True
        else:
            return False

    def _import_db(self, tmpdir):
        """
        Import the rows in each model to the archive.
        """

        # Determine the list of models to exclude
        exclude = getattr(settings, 'ARCHIVE_EXCLUDE', (
            'auth.Permission',
            #'contenttypes.ContentType',
            'sessions.Session',
        ))

        # loads the tables
        call_command('loaddata', str(tmpdir / 'data.json'), format='json', exclude=exclude)

    def _import_files(self, tmpdir):
        """
        Import all uploaded media from the archive.
        """
        mediaroot = Path(getattr(settings, 'MEDIA_ROOT'))
        if not os.path.isdir(str(mediaroot)): os.mkdir(str(mediaroot))

        # Attempt not to cause problems with docker mounted volume (and watchgod
        # from uvicorn) by unzipping just below the mediafiles directory
        for name in tmpdir.glob('mediafiles/*'):
            basename = os.path.basename(name)
            self.stdout.write(self.style.WARNING('Trying to copy {} to {}'.format(str(name),str(mediaroot/basename))))
            shutil.copytree(name, str(mediaroot/basename), dirs_exist_ok=True)

    def _check_meta(self, tar, tmpdir):
        """
        Check metadata  the archive.
        """
        tar.extract('meta.json',str(tmpdir))
        with open(str(tmpdir / 'meta.json')) as data_file:
            data = json.load(data_file)

        if data['version'] != __version__:
             self.stdout.write(self.style.WARNING('The versions don\'t match...continue? (extracted {} : current {})'.format( data["version"], __version__)))

             for c in iter(lambda:input("y/n?"),None):
                 if key == 'n':
                     self.stdout.write(self.style.WARNGING("You selected n"))
                     return False
                 if key == 'y':
                     self.stdout.write(self.style.SUCCESS("You selected y"))
                     return True

        return True

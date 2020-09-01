from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save


class TriviaConfig(AppConfig):
    name = "trivianator.trivia"
    verbose_name = _("Trivia")

    def ready(self):
        try:
            import trivianator.trivia.signals as tsignals # noqa F401
            from trivianator.trivia.models import ArchiveUpload # noqa F401

            #Archive Upload Post save
            post_save.connect(tsignals.archive_upload_post_save, sender=ArchiveUpload)

        except ImportError:
            pass

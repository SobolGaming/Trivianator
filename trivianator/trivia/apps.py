from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class TriviaConfig(AppConfig):
    name = "trivianator.trivia"
    verbose_name = _("Trivia")

    def ready(self):
        try:
            import trivianator.trivia.signals as tsignals # noqa F401

            #Archive Upload Post save
            post_save.connect(tsignals.archive_upload_post_save, sender=ArchiveUpload)

        except ImportError:
            pass

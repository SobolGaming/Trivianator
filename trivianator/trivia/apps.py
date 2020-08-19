from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class TriviaConfig(AppConfig):
    name = "trivianator.trivia"
    verbose_name = _("Trivia")

    def ready(self):
        try:
            import trivianator.trivia.signals  # noqa F401
        except ImportError:
            pass

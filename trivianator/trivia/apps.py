from django.apps import AppConfig


class TriviaConfig(AppConfig):
    name = "trivianator.trivia"
    verbose_name = _("Trivia")

    def ready(self):
        try:
            import trivianator.trivia.signals  # noqa F401
        except ImportError:
            pass

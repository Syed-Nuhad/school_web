# reportcards/apps.py
from django.apps import AppConfig

class ReportcardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reportcards"

    def ready(self):
        # ensures our post_save/post_delete receivers are registered
        from . import signals  # noqa: F401

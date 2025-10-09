from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Lazy imports to avoid circulars during migrations
        from django.db.models.signals import post_save
        from django.contrib.auth import get_user_model

        # Use the new helper
        from content.billing import ensure_monthly_window_for_user

        User = get_user_model()

        def _ensure_monthlies(sender, instance, created, **kwargs):
            # When a user is created, ensure their invoice window exists
            if created:
                try:
                    ensure_monthly_window_for_user(instance)
                except Exception:
                    # never block app startup
                    pass

        post_save.connect(
            _ensure_monthlies,
            sender=User,
            dispatch_uid="ensure_invoices_on_user_create",
        )
# content/middleware/dues_autoqueue.py
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from content.services.dues_autoqueue import queue_overdue_dues_emails

class DuesAutoQueueMiddleware:
    """
    On any request, at most once per interval:
      - queue emails for overdue invoices
    Autosend middleware (which runs after this) will deliver them.
    """
    CACHE_KEY = "dues_autoqueue:last_run"

    def __init__(self, get_response):
        self.get_response = get_response
        self.interval_min = int(getattr(settings, "DUES_SCAN_INTERVAL_MINUTES", 60))
        self.throttle_min = int(getattr(settings, "DUES_EMAIL_THROTTLE_MINUTES", 60))
        self.template_slug = getattr(settings, "DUES_EMAIL_TEMPLATE", "dues_notice_email")

    def __call__(self, request):
        # Run before view, but cheap due to cache guard
        self._maybe_run()
        return self.get_response(request)

    def _maybe_run(self):
        last = cache.get(self.CACHE_KEY)
        now = timezone.now()
        if last and (now - last).total_seconds() < self.interval_min * 60:
            return

        # Run the scan (swallow errors to avoid breaking requests)
        try:
            queue_overdue_dues_emails(
                template_slug=self.template_slug,
                throttle_minutes=self.throttle_min,
            )
        finally:
            cache.set(self.CACHE_KEY, now, timeout=self.interval_min * 60)

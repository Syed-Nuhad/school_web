# content/middleware/comms_autosend.py
import time
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

_last_run_ts = 0.0

class CommsAutoSendMiddleware(MiddlewareMixin):
    """
    Every request, at most once per COMMS_AUTOSEND_MIN_INTERVAL seconds, process a small
    batch of queued emails. Zero external schedulers needed.
    """
    def process_request(self, request):
        global _last_run_ts
        if not getattr(settings, "COMMS_AUTOSEND_EMAIL", False):
            return  # feature off

        min_interval = int(getattr(settings, "COMMS_AUTOSEND_MIN_INTERVAL", 60))
        now = time.time()
        if now - _last_run_ts < max(10, min_interval):  # clamp to ≥10s for sanity
            return

        _last_run_ts = now
        try:
            from content.services.comms_outbox import process_email_batch
            # small batch so we never slow down requests
            process_email_batch(limit=25)
        except Exception:
            # swallow errors to avoid breaking requests
            pass

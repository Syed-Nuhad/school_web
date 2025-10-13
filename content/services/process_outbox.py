from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.template import Template, Context

from content.models import SmsOutbox, CommsLog
from content.services.comms_outbox import process_email_batch  # must accept ignore_throttle


def _render(tpl_str: str, ctx: dict) -> str:
    try:
        return Template(tpl_str or "").render(Context(ctx or {})).strip()
    except Exception:
        return (tpl_str or "")


class Command(BaseCommand):
    help = "Process outbox for SMS/Email. Inline SMS; email via services.comms_outbox."

    def add_arguments(self, parser):
        parser.add_argument("--only", choices=["sms", "email", "both"], default="both")
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--ignore-throttle", action="store_true")  # <-- add this

    def handle(self, *args, **opts):
        only = opts["only"]
        limit = int(opts["limit"])
        ignore_throttle = bool(opts.get("ignore_throttle", False))     # <-- read it

        sms_sent = 0
        email_sent = 0

        if only in ("sms", "both"):
            sms_sent = self._process_sms(limit)

        if only in ("email", "both"):
            # delegate to your email batch sender; pass through the flag
            email_sent = process_email_batch(limit=limit, ignore_throttle=ignore_throttle)

        if only == "sms":
            self.stdout.write(f"SMS sent: {sms_sent}")
            self.stdout.write(f"Total processed: {sms_sent}")
        elif only == "email":
            self.stdout.write(f"Email sent: {email_sent}")
            self.stdout.write(f"Total processed: {email_sent}")
        else:
            self.stdout.write(f"SMS sent: {sms_sent}")
            self.stdout.write(f"Email sent: {email_sent}")
            self.stdout.write(f"Total processed: {sms_sent + email_sent}")

    # ------------------------- SMS processor (inline) -------------------------
    def _process_sms(self, limit: int) -> int:
        provider_default = getattr(settings, "SMS_PROVIDER", "console")

        qs = (
            SmsOutbox.objects
            .select_related("template")
            .exclude(status__in=["sent", "failed"])
            .order_by("id")[:limit]
        )
        self.stdout.write(f"[debug] sms candidates: {qs.count()}")

        sent = 0
        for row in qs:
            provider = row.provider or provider_default

            # respect schedule
            if row.scheduled_at and row.scheduled_at > timezone.now():
                continue

            ctx = row.context or {}
            tpl = row.template
            body_text = _render(getattr(tpl, "body_text_template", "") or "", ctx)

            try:
                with transaction.atomic():
                    if provider == "console":
                        self.stdout.write(
                            f"[SMS console] to={row.to} sender_id={row.sender_id} :: {body_text}"
                        )
                        row.status = "sent"
                        row.sent_at = timezone.now()
                        row.attempts = (row.attempts or 0) + 1
                        row.provider_ref = row.provider_ref or "console-ok"
                        row.save(update_fields=["status", "sent_at", "attempts", "provider_ref"])

                        CommsLog.objects.create(
                            when=row.sent_at,
                            channel="sms",
                            recipient=row.to,
                            template_slug=getattr(tpl, "slug", "") or "",
                            status="sent",
                            detail="1",
                        )

                        sent += 1
                    else:
                        row.status = "failed"
                        row.attempts = (row.attempts or 0) + 1
                        row.provider_ref = "unsupported-provider"
                        row.save(update_fields=["status", "attempts", "provider_ref"])
                        CommsLog.objects.create(
                            when=timezone.now(),
                            channel="sms",
                            recipient=row.to,
                            template_slug=getattr(tpl, "slug", "") or "",
                            status="failed",
                            detail=f"Provider '{provider}' not implemented",
                        )

            except Exception as e:
                row.status = "failed"
                row.attempts = (row.attempts or 0) + 1
                row.provider_ref = f"error:{type(e).__name__}"
                row.save(update_fields=["status", "attempts", "provider_ref"])
                CommsLog.objects.create(
                    when=timezone.now(),
                    channel="sms",
                    recipient=getattr(row, "to", ""),
                    template_slug=getattr(tpl, "slug", "") if 'tpl' in locals() else "",
                    status="failed",
                    detail=str(e)[:300],
                )

        return sent

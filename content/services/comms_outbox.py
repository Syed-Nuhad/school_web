from __future__ import annotations
import math
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone


from .comms_templating import render_string
from .sms import send_sms
from .emailing import send_email_smtp
from ..models import SmsOutbox, OutboxStatus, EmailOutbox, MessageTemplate, CommsLog


def throttle_guard_sms(to: str, template_slug: str) -> bool:
    window = timezone.now() - timedelta(minutes=getattr(settings, "COMMS_THROTTLE_MINUTES", 10))
    return SmsOutbox.objects.filter(
        to=to, template__slug=template_slug, status=OutboxStatus.SENT, sent_at__gte=window
    ).exists()

def throttle_guard_email(to: str, template_slug: str) -> bool:
    window = timezone.now() - timedelta(minutes=getattr(settings, "COMMS_THROTTLE_MINUTES", 10))
    return EmailOutbox.objects.filter(
        to=to, template__slug=template_slug, status=OutboxStatus.SENT, sent_at__gte=window
    ).exists()



def queue_sms(*, to, template_slug, context, created_by=None, provider=None, sender_id=None, scheduled_at=None):
    tpl = MessageTemplate.objects.get(slug=template_slug, kind="sms", is_active=True)
    row = SmsOutbox.objects.create(
        to=str(to).strip(),
        template=tpl,
        context=context or {},
        provider=provider or getattr(settings, "SMS_PROVIDER", "console"),
        sender_id=sender_id or getattr(settings, "SMS_SENDER_ID", ""),
        status=OutboxStatus.QUEUED,
        scheduled_at=scheduled_at or timezone.now(),   # <- never NULL
        created_by=created_by,
    )
    return row



def queue_email(*, to: str, template_slug: str, context: dict,
                from_email: str | None = None, reply_to: str | None = None,
                created_by=None, scheduled_at=None) -> EmailOutbox:
    """
    Enqueue an email and (optionally) kick a small batch sender immediately
    after the DB transaction commits.
    """
    tpl = MessageTemplate.objects.get(slug=template_slug, kind="email", is_active=True)

    ob = EmailOutbox.objects.create(
        to=(to or "").strip(),
        template=tpl,
        context=context or {},
        from_email=from_email or "",
        reply_to=reply_to or "",
        created_by=created_by,
        status=getattr(OutboxStatus, "QUEUED", "queued"),
        scheduled_at=scheduled_at or timezone.now(),
    )

    # lightweight auto-send nudge (no external app)
    if getattr(settings, "COMMS_AUTOSEND_EMAIL", False):
        from .comms_outbox import process_email_batch  # safe local import

        # run AFTER the outer transaction commits so we see the row
        transaction.on_commit(lambda: process_email_batch(limit=20))

    return ob


def _backoff_delay(attempts: int) -> int:
    # 1, 2, 4, 8, 16, 32 mins up to max
    return min(32, 2 ** max(0, attempts - 1))


def process_sms_batch(limit: int = 100) -> int:
    now = timezone.now()
    qs = SmsOutbox.objects.select_for_update(skip_locked=True).filter(
        status__in=[OutboxStatus.QUEUED, OutboxStatus.FAILED],
        scheduled_at__lte=timezone.now(),
    ).order_by("scheduled_at")[:limit]

    count = 0
    with transaction.atomic():
        for ob in qs:
            # throttle per recipient+template
            if throttle_guard_sms(ob.to, ob.template.slug):
                continue
            ob.status = OutboxStatus.SENDING
            ob.save(update_fields=["status"])

    # process outside outer transaction to avoid long locks
    for ob in SmsOutbox.objects.filter(status=OutboxStatus.SENDING).order_by("scheduled_at")[:limit]:
        try:
            body = render_string(ob.template.body_text_template, ob.context)
            provider, ref = send_sms(to=ob.to, sender_id=ob.sender_id, body=body)
            ob.provider = provider
            ob.provider_ref = ref
            ob.status = OutboxStatus.SENT
            ob.sent_at = timezone.now()
            ob.last_error = ""
            ob.save(update_fields=["provider", "provider_ref", "status", "sent_at", "last_error"])
            CommsLog.objects.create(channel="sms", recipient=ob.to, template_slug=ob.template.slug, status="sent", detail=ref or "")
            count += 1
        except Exception as e:
            ob.attempts += 1
            delay = _backoff_delay(ob.attempts)
            ob.next_attempt_at = timezone.now() + timedelta(minutes=delay)
            ob.status = OutboxStatus.FAILED
            ob.last_error = str(e)[:1000]
            ob.scheduled_at = ob.next_attempt_at
            ob.save(update_fields=["attempts", "next_attempt_at", "status", "last_error", "scheduled_at"])
            CommsLog.objects.create(channel="sms", recipient=ob.to, template_slug=ob.template.slug, status="failed", detail=ob.last_error)
    return count

def process_email_batch(limit: int = 100, ignore_throttle: bool = False) -> int:
    now = timezone.now()
    qs = EmailOutbox.objects.select_for_update(skip_locked=True).filter(
        status__in=[OutboxStatus.QUEUED, OutboxStatus.FAILED],
        scheduled_at__lte=now,
    ).order_by("scheduled_at")[:limit]

    count = 0
    with transaction.atomic():
        for ob in qs:
            # respect throttle unless explicitly ignored
            if (not ignore_throttle) and throttle_guard_email(ob.to, ob.template.slug):
                continue
            ob.status = OutboxStatus.SENDING
            ob.save(update_fields=["status"])

    # process the ones moved to SENDING
    for ob in EmailOutbox.objects.filter(status=OutboxStatus.SENDING).order_by("scheduled_at")[:limit]:
        try:
            subject = render_string(ob.template.subject_template, ob.context)
            body_text = render_string(ob.template.body_text_template, ob.context)
            body_html = render_string(ob.template.body_html_template, ob.context) if ob.template.body_html_template else None
            msg_id = send_email_smtp(
                to=ob.to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                from_email=(ob.from_email or None),
                reply_to=(ob.reply_to or None),
            )
            ob.provider = "smtp"
            ob.provider_ref = msg_id
            ob.status = OutboxStatus.SENT
            ob.sent_at = timezone.now()
            ob.last_error = ""
            ob.save(update_fields=["provider", "provider_ref", "status", "sent_at", "last_error"])
            CommsLog.objects.create(channel="email", recipient=ob.to, template_slug=ob.template.slug, status="sent", detail=msg_id)
            count += 1
        except Exception as e:
            ob.attempts += 1
            delay = _backoff_delay(ob.attempts)
            ob.next_attempt_at = timezone.now() + timedelta(minutes=delay)
            ob.status = OutboxStatus.FAILED
            ob.last_error = str(e)[:1000]
            ob.scheduled_at = ob.next_attempt_at
            ob.save(update_fields=["attempts", "next_attempt_at", "status", "last_error", "scheduled_at"])
            CommsLog.objects.create(channel="email", recipient=ob.to, template_slug=ob.template.slug, status="failed", detail=ob.last_error)
    return count




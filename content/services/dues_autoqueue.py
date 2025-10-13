# content/services/dues_autoqueue.py
from datetime import timedelta
from decimal import Decimal
from django.db.models import F
from django.utils import timezone

from content.models import TuitionInvoice, CommsLog
from content.services.comms_outbox import queue_email

def queue_overdue_dues_emails(*, template_slug: str = "dues_notice_email",
                              throttle_minutes: int = 60) -> int:
    """
    Find invoices that are due and unpaid, and queue one email per invoice,
    unless we recently emailed the same recipient with the same template.
    Returns count of emails queued.
    """
    now = timezone.now()
    today = timezone.localdate()

    # Unpaid & due (monthly or custom)
    qs = (
        TuitionInvoice.objects
        .select_related("student")
        .filter(tuition_amount__gt=F("paid_amount"))
        .filter(due_date__isnull=False, due_date__lte=today)
        .order_by("-period_year", "-period_month", "-id")
    )

    throttle_window = now - timedelta(minutes=throttle_minutes)
    queued = 0

    for inv in qs:
        student = inv.student
        to_email = (getattr(student, "email", "") or "").strip()
        if not to_email:
            continue

        # Has a recent sent email for this recipient+template?
        recently_sent = CommsLog.objects.filter(
            channel="email",
            status="sent",
            recipient=to_email,
            template_slug=template_slug,
            when__gte=throttle_window,
        ).exists()
        if recently_sent:
            continue

        amount = inv.tuition_amount or Decimal("0")
        paid   = inv.paid_amount or Decimal("0")
        due    = amount - paid
        if due <= 0:
            continue

        ctx = {
            "student_name": (getattr(student, "get_full_name", lambda: "")() or student.username),
            "amount_due": f"{due:.2f}",
            "due_date": inv.due_date.isoformat() if inv.due_date else "—",
            "period": (
                f"{inv.period_year}-{int(inv.period_month):02d}"
                if inv.kind == "monthly" and inv.period_year and inv.period_month
                else (inv.title or "Invoice")
            ),
        }

        queue_email(
            to=to_email,
            template_slug=template_slug,  # must exist in admin with Kind="email"
            context=ctx,
            # from_email / reply_to optional:
            # from_email="Accounts <accounts@yourdomain.tld>",
            # reply_to="accounts@yourdomain.tld",
        )
        queued += 1

    return queued
    
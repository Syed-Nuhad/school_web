# content/management/commands/queue_dues_notices.py

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone

from content.models import TuitionInvoice
from content.services.comms_outbox import queue_sms, queue_email


def _resolve_phone(user):
    """
    Try common fields to find a student's reachable phone number.
    Adjust the list if your project uses different names.
    """
    def pick(*paths):
        for path in paths:
            obj = user
            for part in path.split("."):
                obj = getattr(obj, part, None)
                if obj is None:
                    break
            if obj:
                s = str(obj).strip()
                if s:
                    return s
        return None

    raw = pick(
        "phone", "mobile", "contact_number",
        "studentprofile.phone",
        "studentprofile.guardian_phone",
        "studentprofile.father_phone",
        "studentprofile.mother_phone",
        "studentprofile.emergency_phone",
    )
    if not raw:
        return None

    # very light normalization → +88 for BD-style numbers
    import re
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith("0") and not digits.startswith("+"):
        digits = "+88" + digits
    if not digits.startswith("+"):
        # last resort: assume BD
        if 10 <= len(digits) <= 13:
            digits = "+88" + digits
        else:
            return None
    return digits


class Command(BaseCommand):
    help = "Queue dues notices (SMS/Email) for students with outstanding invoices."

    def add_arguments(self, parser):
        parser.add_argument("--send-sms", action="store_true", help="Queue SMS notices")
        parser.add_argument("--send-email", action="store_true", help="Queue Email notices")
        parser.add_argument("--only-overdue", action="store_true", help="Only invoices with balance > 0")
        parser.add_argument("--limit", type=int, default=1000)

    def handle(self, *args, **options):
        # base queryset: invoices (latest first)
        qs = TuitionInvoice.objects.select_related("student").order_by("-period_year", "-period_month", "-id")

        if options.get("only_overdue"):
            qs = qs.filter(tuition_amount__gt=F("paid_amount"))

        if options.get("limit"):
            qs = qs[: options["limit"]]

        sms_q = 0
        email_q = 0

        for inv in qs:
            student = inv.student
            amount = inv.tuition_amount or Decimal("0.00")
            paid = inv.paid_amount or Decimal("0.00")
            due = amount - paid
            if due <= 0:
                continue

            ctx = {
                "student_name": (getattr(student, "get_full_name", lambda: "")() or student.username),
                "amount_due": f"{due:.2f}",
                "due_date": (inv.due_date.isoformat() if inv.due_date else "—"),
                "period": (
                    f"{inv.period_year}-{int(inv.period_month):02d}"
                    if inv.kind == "monthly" and inv.period_year and inv.period_month else (inv.title or "Invoice")
                ),
            }

            # EMAIL
            if options.get("send_email"):
                to_email = (getattr(student, "email", "") or "").strip()
                if to_email:

                    # AFTER
                    queue_email(
                        to=to_email,
                        template_slug="dues_notice_email",  # <-- matches your admin template
                        context=ctx,
                    )
                    email_q += 1

            # SMS
            if options.get("send_sms"):
                phone = _resolve_phone(student)
                if phone:
                    queue_sms(to=phone, template_slug="dues_notice", context=ctx, created_by=None)
                    sms_q += 1

        self.stdout.write(self.style.SUCCESS(f"Queued SMS: {sms_q}  |  Queued Email: {email_q}"))

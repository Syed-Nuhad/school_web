# content/billing.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import TuitionInvoice, StudentProfile, TuitionPayment


# ----------------------------
# Internal month helpers
# ----------------------------
def _ym_today() -> tuple[int, int]:
    """Return (year, month) for local date."""
    d = timezone.localdate()
    return d.year, d.month


def _next_ym(year: int, month: int) -> tuple[int, int]:
    """Return (year, month) for the next month."""
    return (year + 1, 1) if month == 12 else (year, month + 1)


# ----------------------------
# Fee resolution
# ----------------------------
def monthly_fee_for_user(user) -> Decimal:
    """
    Resolve monthly fee with this order:
      1) StudentProfile.monthly_fee  (if present and > 0)
      2) StudentProfile.school_class.monthly_fee  (if your AcademicClass has this field)
      3) settings.DEFAULT_MONTHLY_FEE (fallback, e.g. 2000)

    Works even if your models don't have those 'monthly_fee' fields — it will
    just use the fallback.
    """
    prof = (
        StudentProfile.objects
        .select_related("school_class")
        .filter(user=user)
        .only("monthly_fee", "school_class_id")
        .first()
    )

    # 1) per student
    if prof is not None and hasattr(prof, "monthly_fee") and prof.monthly_fee:
        try:
            val = Decimal(prof.monthly_fee)
            if val > 0:
                return val
        except Exception:
            pass

    # 2) per class (optional)
    sc = getattr(prof, "school_class", None) if prof else None
    if sc is not None and hasattr(sc, "monthly_fee") and sc.monthly_fee:
        try:
            val = Decimal(sc.monthly_fee)
            if val > 0:
                return val
        except Exception:
            pass

    # 3) global fallback
    fallback = getattr(settings, "DEFAULT_MONTHLY_FEE", 2000)
    try:
        return Decimal(str(fallback))
    except Exception:
        return Decimal("0")


# ----------------------------
# Invoice ensuring / creation
# ----------------------------
@transaction.atomic
def get_or_create_month_invoice(user, year: int, month: int) -> TuitionInvoice:
    """
    Create or fetch a monthly invoice for (user, year, month).
    Keeps tuition_amount in sync with the current configured fee
    when invoice is still unpaid.
    """
    inv, _ = (
        TuitionInvoice.objects
        .select_for_update()
        .get_or_create(
            student=user,
            kind="monthly",
            period_year=year,
            period_month=month,
            defaults={
                "tuition_amount": monthly_fee_for_user(user),
                "paid_amount": Decimal("0.00"),
            },
        )
    )

    expected = monthly_fee_for_user(user)
    # Only update amount automatically if no money has been paid yet
    if inv.paid_amount in (None, Decimal("0")) and inv.tuition_amount != expected:
        inv.tuition_amount = expected
        inv.save(update_fields=["tuition_amount"])
    return inv


@transaction.atomic
def ensure_monthly_window_for_user(user, months_ahead: int = 1) -> tuple[TuitionInvoice, TuitionInvoice | None]:
    """
    Ensure the current month's invoice exists, plus `months_ahead` future months.
    Example: months_ahead=1 ensures current + next month.
    Returns (current_invoice, last_future_invoice_or_none).
    """
    y, m = _ym_today()
    current = get_or_create_month_invoice(user, y, m)

    last = None
    ay, am = y, m
    for _ in range(months_ahead):
        ay, am = _next_ym(ay, am)
        last = get_or_create_month_invoice(user, ay, am)

    return current, last


def ensure_current_month_invoice(user) -> TuitionInvoice:
    """
    Convenience used by signals: just make sure THIS month's invoice exists.
    """
    y, m = _ym_today()
    return get_or_create_month_invoice(user, y, m)


# ----------------------------
# Dues summary (for UI)
# ----------------------------
@dataclass
class DuesSummary:
    total_due: Decimal
    unpaid_count: int
    unpaid: list  # list[TuitionInvoice]
    upcoming: TuitionInvoice | None

def compute_dues_summary(user) -> DuesSummary:
    """
    - ensures only current + next month exist (once),
    - DOES NOT create any additional “upcoming” invoices,
    - returns total due + unpaid list.
    """
    # ensure current + ONE future month exist
    current, next_inv = ensure_monthly_window_for_user(user, months_ahead=1)

    qs = (
        TuitionInvoice.objects
        .filter(student=user)
        .order_by("period_year", "period_month", "id")
    )

    unpaid = [i for i in qs if (i.paid_amount or 0) < (i.tuition_amount or 0)]
    total_due = sum(
        ((i.tuition_amount or Decimal("0")) - (i.paid_amount or Decimal("0")))
        for i in unpaid
    )

    # IMPORTANT: don't create anything new here; just show the next one we already ensured
    upcoming = next_inv

    return DuesSummary(
        total_due=total_due,
        unpaid_count=len(unpaid),
        unpaid=unpaid,
        upcoming=upcoming,
    )

# ----------------------------
# Bulk allocation (pay all dues)
# ----------------------------
@transaction.atomic
def allocate_payment_across_invoices(
    user,
    amount: Decimal,
    *,
    provider: str,
    txn_id: str | None = None,
) -> list[TuitionPayment]:
    """
    Take a single 'amount' and spread it across this student's unpaid invoices
    (oldest → newest). Creates TuitionPayment rows and updates each invoice.paid_amount.
    Returns the list of TuitionPayment created.
    """
    if amount is None or Decimal(amount) <= 0:
        return []

    # Oldest first
    invoices = (
        TuitionInvoice.objects
        .select_for_update()
        .filter(student=user)
        .order_by("period_year", "period_month", "id")
    )

    remaining = Decimal(amount)
    created: list[TuitionPayment] = []

    for inv in invoices:
        bal = (inv.tuition_amount or Decimal("0")) - (inv.paid_amount or Decimal("0"))
        if bal <= 0:
            continue
        if remaining <= 0:
            break

        pay_now = min(bal, remaining)

        tp = TuitionPayment.objects.create(
            invoice=inv,
            amount=pay_now,
            provider=provider,
            txn_id=txn_id,  # may be None for internal/instant payments
            paid_on=timezone.localdate(),
        )
        created.append(tp)

        inv.paid_amount = (inv.paid_amount or Decimal("0")) + pay_now
        inv.save(update_fields=["paid_amount"])

        remaining -= pay_now

    return created


def create_custom_invoice(user, *, title: str, amount, due_date=None) -> TuitionInvoice:
    """
    Create a 'custom' invoice for a single student.
    - amount may be str/Decimal/float; we'll coerce to Decimal.
    - due_date defaults to today if not provided.
    """
    amt = Decimal(str(amount))
    inv = TuitionInvoice.objects.create(
        student=user,
        kind="custom",
        title=title.strip(),
        tuition_amount=amt,
        paid_amount=Decimal("0"),
        due_date=due_date or timezone.localdate(),
    )
    return inv
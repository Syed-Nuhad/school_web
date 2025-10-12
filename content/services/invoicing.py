# content/services/invoicing.py
from __future__ import annotations
from decimal import Decimal
from datetime import date

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from ..models import TuitionInvoice

def _next_year_month(y: int, m: int) -> tuple[int, int]:
    if m == 12:
        return (y + 1, 1)
    return (y, m + 1)

@transaction.atomic
def ensure_monthly_invoice_for_student(student, year: int, month: int, amount: Decimal) -> TuitionInvoice:
    """
    Create (or fetch) a 'monthly' invoice for given student/year/month.
    Idempotent: returns existing if already there.
    """
    inv, _ = TuitionInvoice.objects.get_or_create(
        student=student,
        kind="monthly",
        period_year=year,
        period_month=month,
        defaults={
            "tuition_amount": amount,
        },
    )
    # if amount changed later, you can choose to sync it:
    # if inv.tuition_amount != amount and inv.paid_amount == 0:
    #     inv.tuition_amount = amount
    #     inv.save(update_fields=["tuition_amount"])
    return inv

@transaction.atomic
def backfill_missing_monthlies(student, start_year: int, start_month: int, end_year: int, end_month: int, amount: Decimal) -> int:
    """
    Ensure every month in [start, end] exists for the student.
    Returns count created.
    """
    y, m = start_year, start_month
    created = 0
    while (y < end_year) or (y == end_year and m <= end_month):
        inv, made = TuitionInvoice.objects.get_or_create(
            student=student,
            kind="monthly",
            period_year=y,
            period_month=m,
            defaults={"tuition_amount": amount},
        )
        if made:
            created += 1
        # next month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return created

def upcoming_month_for(date_ref: date | None = None) -> tuple[int, int]:
    d = date_ref or date.today()
    return _next_year_month(d.year, d.month)

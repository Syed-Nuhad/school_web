# content/views.py
from __future__ import annotations

import csv
import decimal
import json
import uuid
import stripe
import requests


from decimal import Decimal
from typing import Dict

from django.contrib.auth import get_user_model
from django.db.models import Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.db.models import Sum, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    HttpResponse, HttpResponseForbidden, Http404, HttpRequest, HttpResponseNotAllowed,
)

from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.generic import DetailView, CreateView

from .billing import ensure_monthly_window_for_user, compute_dues_summary, allocate_payment_across_invoices
from .decorators import teacher_or_admin_required
from .forms import AdmissionApplicationForm
from .models import (
    Banner,
    Notice,
    TimelineEvent,
    Course,
    AdmissionApplication,
    Income,
    Expense,
    TuitionInvoice,
    TuitionPayment,
    IncomeCategory,
    AcademicClass,
    StudentProfile, PaymentReceipt,
)

# --------------------------------------------------------------------------------------
# Payments config guard (so imports don’t crash when not configured)
# --------------------------------------------------------------------------------------
P = getattr(settings, "PAYMENTS", {})
PP_READY = all(P.get(k) for k in ("PP_BASE", "PP_CLIENT", "PP_SECRET"))
User = get_user_model()
# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------
def _image_src(file_field, fallback_url: str | None) -> str:
    """Prefer uploaded file URL; otherwise use the provided external URL; else empty."""
    if file_field:
        try:
            return file_field.url
        except Exception:
            pass
    return (fallback_url or "").strip()


def _json_bad(msg, code=400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": msg}, status=code)


def _json_ok(**k) -> JsonResponse:
    return JsonResponse({"ok": True, **k})


# --------------------------------------------------------------------------------------
# Public read APIs (homepage data)
# --------------------------------------------------------------------------------------
@require_GET
def api_slides(request):
    """Banners for hero slider."""
    items = Banner.objects.filter(is_active=True).order_by("order", "-created_at")
    data = [
        {
            "id": b.id,
            "title": b.title,
            "caption": b.subtitle,
            "subtitle": b.subtitle,
            "image": _image_src(b.image, b.image_url),
            "order": b.order,
            "button_text": b.button_text,
            "button_link": b.button_link,
        }
        for b in items
    ]
    return JsonResponse({"items": data})


@require_GET
def api_notices(request):
    """?limit=3 to restrict number of notices."""
    qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")
    try:
        limit = int(request.GET.get("limit", "0"))
    except ValueError:
        limit = 0
    if limit > 0:
        qs = qs[:limit]

    data = [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "image": _image_src(n.image, n.image_url),
            "link_url": (n.link_url or "").strip(),
            "grade": (n.grade or "").strip() if hasattr(n, "grade") else "",
            "section": (n.section or "").strip() if hasattr(n, "section") else "",
            "posted_by": (n.posted_by.username if getattr(n, "posted_by", None) else None),
        }
        for n in qs
    ]
    return JsonResponse({"items": data})


@require_GET
def api_timeline(request):
    qs = TimelineEvent.objects.filter(is_active=True).order_by("date", "order")[:3]
    data = [
        {
            "id": e.id,
            "title": e.title,
            "date": e.date.isoformat(),
            "description": e.description,
            "order": e.order,
        }
        for e in qs
    ]
    return JsonResponse({"items": data})


# --------------------------------------------------------------------------------------
# Manage endpoints (teacher/admin)
# --------------------------------------------------------------------------------------
@teacher_or_admin_required
@require_POST
def manage_slide_create(request):
    """
    Creates a Banner. Accepts:
      title, subtitle|caption, image(file) or image_url, order, button_text, button_link
    """
    title = (request.POST.get("title") or "").strip()
    subtitle = (request.POST.get("subtitle") or request.POST.get("caption") or "").strip()
    image_url = (request.POST.get("image_url") or "").strip()
    button_text = (request.POST.get("button_text") or "").strip()
    button_link = (request.POST.get("button_link") or "").strip()

    try:
        order = int(request.POST.get("order") or 0)
    except ValueError:
        order = 0

    if not title and not image_url and "image" not in request.FILES:
        return HttpResponseBadRequest("Provide at least a title and an image or image_url.")

    b = Banner(
        title=title,
        subtitle=subtitle,
        image_url=image_url,
        order=order,
        button_text=button_text,
        button_link=button_link,
        created_by=request.user,
    )
    if "image" in request.FILES:
        b.image = request.FILES["image"]
    b.save()
    return JsonResponse({"created": {"id": b.id}}, status=201)


@teacher_or_admin_required
@require_POST
def manage_notice_create(request):
    """
    Creates a Notice.
    Accepts: title (required), body, link_url, image(file)|image_url,
             grade, section (optional if model has fields),
             published_at (ISO datetime or date).
    """
    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    link_url = (request.POST.get("link_url") or "").strip()
    image_url = (request.POST.get("image_url") or "").strip()

    grade = (request.POST.get("grade") or "").strip()
    section = (request.POST.get("section") or "").strip()

    if not title:
        return HttpResponseBadRequest("title is required")

    published_raw = (request.POST.get("published_at") or "").strip()
    published_at = parse_datetime(published_raw) or parse_date(published_raw) if published_raw else None

    n = Notice(
        title=title,
        body=body,
        link_url=link_url,
        image_url=image_url,
        posted_by=request.user,
    )

    if hasattr(n, "grade"):
        n.grade = grade
    if hasattr(n, "section"):
        n.section = section

    if hasattr(published_at, "isoformat"):  # datetime
        n.published_at = published_at
    elif published_at:  # date
        from datetime import datetime
        n.published_at = datetime.combine(published_at, datetime.min.time())

    if "image" in request.FILES:
        n.image = request.FILES["image"]

    if not n.published_at:
        n.published_at = timezone.now()

    n.save()
    return JsonResponse({"created": {"id": n.id}}, status=201)


@teacher_or_admin_required
@require_POST
def manage_timeline_create(request):
    """
    Creates a TimelineEvent.
    Accepts: title (required), date (YYYY-MM-DD required), description, order
    """
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    date_raw = (request.POST.get("date") or "").strip()

    try:
        order = int(request.POST.get("order") or 0)
    except ValueError:
        order = 0

    if not title or not date_raw:
        return HttpResponseBadRequest("title and date are required")
    date_obj = parse_date(date_raw)
    if not date_obj:
        return HttpResponseBadRequest("date must be YYYY-MM-DD")

    e = TimelineEvent(
        title=title,
        description=description,
        date=date_obj,
        order=order,
        created_by=request.user,
    )
    e.save()
    return JsonResponse({"created": {"id": e.id}}, status=201)


# --------------------------------------------------------------------------------------
# Admissions flow
# --------------------------------------------------------------------------------------
class AdmissionReviewView(DetailView):
    model = AdmissionApplication
    template_name = "admissions/review.html"
    context_object_name = "application"


class AdmissionApplyView(CreateView):
    """
    Creates a draft application; snapshots fees; redirects to review.
    """
    model = AdmissionApplication
    form_class = AdmissionApplicationForm
    template_name = "admissions/apply.html"

    def get_initial(self):
        initial = super().get_initial()
        course_id = self.request.GET.get("course")
        if course_id:
            try:
                initial["desired_course"] = Course.objects.get(pk=course_id)
            except Course.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        app: AdmissionApplication = form.save(commit=False)
        course = app.desired_course

        # snapshot base fees from course
        app.fee_admission = course.admission_fee or Decimal("0")
        app.fee_tuition = course.first_month_tuition or Decimal("0")
        app.fee_exam = course.exam_fee or Decimal("0")

        # add-ons selected by user (booleans in the form)
        app.fee_bus = (course.bus_fee or Decimal("0")) if app.add_bus else Decimal("0")
        app.fee_hostel = (course.hostel_fee or Decimal("0")) if app.add_hostel else Decimal("0")
        app.fee_marksheet = (course.marksheet_fee or Decimal("0")) if app.add_marksheet else Decimal("0")

        app.fee_total = (
            app.fee_admission
            + app.fee_tuition
            + app.fee_exam
            + app.fee_bus
            + app.fee_hostel
            + app.fee_marksheet
        )

        app.payment_status = "pending"
        app.save()
        return redirect("admissions:review", pk=app.pk)


class AdmissionConfirmView(DetailView):
    """
    Demo: manual mark as paid. Replace with real gateway confirmation later.
    """
    model = AdmissionApplication
    template_name = "admissions/confirm.html"
    context_object_name = "application"

    def post(self, request, *args, **kwargs):
        app: AdmissionApplication = self.get_object()
        app.payment_status = "paid"
        app.payment_method = request.POST.get("method", "manual")
        app.payment_reference = request.POST.get("reference", "")
        app.save()

        # Send simple receipt
        if app.email:
            subject = f"Payment received — {app.desired_course.title}"
            msg = (
                f"Dear {app.full_name},\n\n"
                f"We’ve received your payment for {app.desired_course.title}.\n"
                f"Total paid: BDT {app.fee_total}\n"
                f"Reference: {app.payment_reference or 'N/A'}\n\n"
                f"Thank you.\n"
                f"{getattr(settings, 'INSTITUTION_NAME', 'Your Institution')}"
            )
            send_mail(
                subject,
                msg,
                getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                [app.email],
                fail_silently=True,
            )

        messages.success(request, "Payment confirmed. Receipt is ready.")
        return redirect("admissions:receipt", pk=app.pk)


class AdmissionReceiptView(DetailView):
    model = AdmissionApplication
    template_name = "admissions/receipt.html"
    context_object_name = "application"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "institution_name": getattr(settings, "INSTITUTION_NAME", "Your Institution"),
                "institution_phone": getattr(settings, "INSTITUTION_PHONE", None),
                "institution_email": getattr(settings, "INSTITUTION_EMAIL", None),
                "institution_address": getattr(settings, "INSTITUTION_ADDRESS", None),
                "institution_logo_url": getattr(settings, "INSTITUTION_LOGO_URL", None),
            }
        )
        return ctx


# Amount helper used by front-end to create gateway orders
def _amount_for(app: AdmissionApplication) -> Decimal:
    return app.fee_selected_total or app.fee_total or Decimal("0")


@require_GET
def create_payment_order(request, pk: int):
    """
    Return server-computed amount your frontend should charge via gateway.
    """
    app = get_object_or_404(AdmissionApplication, pk=pk)
    if app.payment_status == "paid":
        return JsonResponse({"error": "already_paid"}, status=400)

    amount = _amount_for(app)
    return JsonResponse(
        {
            "application_id": app.pk,
            "amount": str(amount),
            "currency": "BDT",
            "description": f"Admission fees for {app.full_name}",
        }
    )


@csrf_exempt
@require_POST
def mark_payment_paid(request, pk: int):
    """
    Call this AFTER gateway confirms capture.
    Body JSON: { "provider": "paypal"|"bkash"|"card", "transaction_id": "..." }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = {}

    provider = (data.get("provider") or "").lower()
    txn_id = data.get("transaction_id") or ""

    if provider not in {"paypal", "bkash", "card", "visa", "mastercard"}:
        return JsonResponse({"error": "invalid_provider"}, status=400)
    if not txn_id:
        return JsonResponse({"error": "missing_transaction_id"}, status=400)

    app = get_object_or_404(AdmissionApplication, pk=pk)
    if app.payment_status == "paid":
        return JsonResponse({"status": "already_paid"})

    app.mark_paid(provider, txn_id)  # assumes your model has this helper
    # (Optional) send success email here if not inside mark_paid()
    return JsonResponse({"status": "ok"})


# --------------------------------------------------------------------------------------
# PayPal (dev helper; guarded so missing config won’t 500)
# --------------------------------------------------------------------------------------
def _pp_token() -> str:
    r = requests.post(
        f"{P['PP_BASE']}/v1/oauth2/token",
        auth=(P["PP_CLIENT"], P["PP_SECRET"]),
        data={"grant_type": "client_credentials"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


@csrf_exempt
@require_http_methods(["POST"])
def paypal_create(request):
    if not PP_READY:
        return _json_bad("PayPal not configured", 503)

    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}
    amount = float(data.get("amount") or 0) or 15.00
    currency = data.get("currency") or "USD"

    try:
        token = _pp_token()
        order = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": f"ADM_{uuid.uuid4().hex[:10]}",
                    "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                }
            ],
        }
        r = requests.post(
            f"{P['PP_BASE']}/v2/checkout/orders",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json=order,
            timeout=20,
        )
        r.raise_for_status()
        j = r.json()
        return _json_ok(orderID=j["id"])
    except Exception as e:
        return _json_bad(str(e), 502)


@csrf_exempt
@require_http_methods(["POST"])
def paypal_capture(request):
    if not PP_READY:
        return _json_bad("PayPal not configured", 503)

    try:
        body = json.loads(request.body or "{}")
    except Exception:
        body = {}
    order_id = body.get("orderID")
    if not order_id:
        return _json_bad("Missing orderID")

    try:
        token = _pp_token()
        r = requests.post(
            f"{P['PP_BASE']}/v2/checkout/orders/{order_id}/capture",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            timeout=20,
        )
        r.raise_for_status()
        j = r.json()
        paid = j.get("status") == "COMPLETED"
        return _json_ok(paid=paid, details=j)
    except Exception as e:
        return _json_bad(str(e), 502)


# --------------------------------------------------------------------------------------
# Finance views (dashboard + totals + overview + CSV export)
# --------------------------------------------------------------------------------------
def finance_dashboard(request):
    total_income = Income.objects.aggregate(s=Sum("amount"))["s"] or 0
    total_expense = Expense.objects.aggregate(s=Sum("amount"))["s"] or 0
    balance = total_income - total_expense
    context = {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "incomes": Income.objects.order_by("-date")[:10],
        "expenses": Expense.objects.order_by("-date")[:10],
    }
    return render(request, "finance/dashboard.html", context)


def finance_totals(request):
    """GET ?from=YYYY-MM-DD&to=YYYY-MM-DD → { total_income, total_expense, balance }"""
    today = timezone.localdate()
    d_from = parse_date(request.GET.get("from") or str(today.replace(day=1)))
    d_to = parse_date(request.GET.get("to") or str(today))
    inc = Income.objects.filter(date__range=[d_from, d_to]).aggregate(s=Sum("amount"))["s"] or 0
    exp = Expense.objects.filter(date__range=[d_from, d_to]).aggregate(s=Sum("amount"))["s"] or 0
    return JsonResponse(
        {"from": str(d_from), "to": str(d_to), "total_income": float(inc), "total_expense": float(exp), "balance": float(inc - exp)}
    )


def build_finance_context(request):
    """
    Common builder for the Finance Overview page (admin and public print view).
    Supports ?from=YYYY-MM-DD&to=YYYY-MM-DD&year=YYYY&month=MM
    Also respects session key "finance_outstanding_ids" used by admin action.
    """
    today = timezone.localdate()
    d_from = parse_date(request.GET.get("from") or "") or today.replace(day=1)
    d_to = parse_date(request.GET.get("to") or "") or today

    try:
        year = int(request.GET.get("year") or today.year)
    except Exception:
        year = today.year
    try:
        month = int(request.GET.get("month") or today.month)
    except Exception:
        month = today.month

    total_income = Income.objects.filter(date__range=[d_from, d_to]).aggregate(s=Sum("amount"))["s"] or 0
    total_expense = Expense.objects.filter(date__range=[d_from, d_to]).aggregate(s=Sum("amount"))["s"] or 0
    balance = total_income - total_expense

    income_by_cat = (
        Income.objects.filter(date__range=[d_from, d_to])
        .values(name=F("category__name"))
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    expense_by_cat = (
        Expense.objects.filter(date__range=[d_from, d_to])
        .values(name=F("category__name"))
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    outstanding = (
        TuitionInvoice.objects.filter(period_year=year, period_month=month)
        .exclude(paid_amount=F("tuition_amount"))
        .select_related("student")
        .order_by("period_year", "period_month", "student__username")
    )
    ids = request.session.pop("finance_outstanding_ids", None)
    if ids:
        outstanding = outstanding.filter(id__in=ids)

    return {
        "d_from": d_from,
        "d_to": d_to,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "income_by_cat": list(income_by_cat),
        "expense_by_cat": list(expense_by_cat),
        "outstanding": outstanding,
        "year": year,
        "month": month,
        "title": "Finance Overview",
    }


def finance_overview(request):
    """
    Renders the printable admin-style Overview using the builder above.
    Template: admin/finance/overview.html (the one I gave you).
    """
    ctx = build_finance_context(request)
    ctx["print_mode"] = request.GET.get("print") == "1"
    return render(request, "admin/finance/overview.html", ctx)


def finance_export_csv(request):
    """
    GET ?type=income|expense|outstanding&from=YYYY-MM-DD&to=YYYY-MM-DD&year=YYYY&month=MM
    """
    kind = (request.GET.get("type") or "income").lower()
    today = timezone.localdate()
    d_from = parse_date(request.GET.get("from") or str(today.replace(day=1)))
    d_to = parse_date(request.GET.get("to") or str(today))
    year = int(request.GET.get("year") or today.year)
    month = int(request.GET.get("month") or today.month)

    if kind not in ("income", "expense", "outstanding"):
        kind = "income"

    filename = f"finance_{kind}.csv"
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    w = csv.writer(resp)

    if kind == "income":
        w.writerow(["Date", "Category", "Amount", "Description"])
        qs = Income.objects.filter(date__range=[d_from, d_to]).select_related("category").order_by("date", "id")
        for r in qs:
            w.writerow([r.date, r.category.name if r.category_id else "", r.amount, r.description])
    elif kind == "expense":
        w.writerow(["Date", "Category", "Amount", "Vendor", "Description"])
        qs = Expense.objects.filter(date__range=[d_from, d_to]).select_related("category").order_by("date", "id")
        for r in qs:
            w.writerow([r.date, r.category.name if r.category_id else "", r.amount, r.vendor, r.description])
    else:
        w.writerow(["Student", "Year", "Month", "Tuition", "Paid", "Balance", "Due Date"])
        qs = (
            TuitionInvoice.objects.filter(period_year=year, period_month=month)
            .exclude(paid_amount=F("tuition_amount"))
            .select_related("student")
            .order_by("student_id")
        )
        for inv in qs:
            w.writerow(
                [str(inv.student), inv.period_year, inv.period_month, inv.tuition_amount, inv.paid_amount, inv.balance, inv.due_date or ""]
            )
    return resp


# --------------------------------------------------------------------------------------
# Student quick lookup builder (for your student ledger page)
# --------------------------------------------------------------------------------------
def build_student_lookup_context(request):
    classes = AcademicClass.objects.order_by("-year", "name")
    roll = (request.GET.get("roll") or "").strip()
    class_id = (request.GET.get("class") or "").strip()
    section = (request.GET.get("section") or "").strip()

    ctx = {"classes": classes, "roll": roll, "class_id": class_id, "section": section, "result": None, "error": ""}

    if roll and class_id:
        try:
            profile = StudentProfile.objects.select_related("user", "school_class").get(
                school_class_id=int(class_id),
                section__iexact=section,  # case-insensitive to match admin view
                roll_number=int(roll),
            )
        except StudentProfile.DoesNotExist:
            ctx["error"] = "No student found for that Class/Section/Roll."
            return ctx

        invoices = TuitionInvoice.objects.filter(student=profile.user)
        months_paid = invoices.filter(paid_amount__gte=F("tuition_amount")).count()
        months_due = invoices.filter(paid_amount__lt=F("tuition_amount")).count()
        total_due = invoices.aggregate(s=Sum(F("tuition_amount") - F("paid_amount")))["s"] or 0
        total_paid = invoices.aggregate(s=Sum("paid_amount"))["s"] or 0

        exam_cat = IncomeCategory.objects.filter(code="exam").first()
        bus_cat = IncomeCategory.objects.filter(code="bus").first()
        exam_total = Income.objects.filter(student=profile.user, category=exam_cat).aggregate(s=Sum("amount"))["s"] or 0 if exam_cat else 0
        bus_total = Income.objects.filter(student=profile.user, category=bus_cat).aggregate(s=Sum("amount"))["s"] or 0 if bus_cat else 0

        ctx["result"] = {
            "profile": profile,
            "months_paid": months_paid,
            "months_due": months_due,
            "total_paid": total_paid,
            "total_due": total_due,
            "exam_total": exam_total,
            "bus_total": bus_total,
            "recent_invoices": invoices.order_by("-period_year", "-period_month")[:12],
        }
    return ctx


# --------------------------------------------------------------------------------------
# Admission → Income (categoryized rows when application becomes paid)
# --------------------------------------------------------------------------------------
def _income_cat(code: str, fallback_name: str) -> IncomeCategory:
    cat, _ = IncomeCategory.objects.get_or_create(code=code, defaults={"name": fallback_name, "is_fixed": True})
    return cat


@receiver(post_save, sender=AdmissionApplication)
def _post_income_when_admission_paid(sender, instance: AdmissionApplication, created, **kwargs):
    """
    When an AdmissionApplication is paid, drop Income rows for selected items (admission/tuition/bus/exam...).
    Prevents duplicate inserts by checking a TXN tag in description.
    """
    if instance.payment_status != "paid":
        return

    tag = f"TXN:{instance.payment_txn_id}" if getattr(instance, "payment_txn_id", "") else None
    if tag and Income.objects.filter(description__icontains=tag).exists():
        return

    rows: list[tuple[str, Decimal, str]] = []

    if getattr(instance, "add_admission", False) and (instance.fee_admission or 0) > 0:
        rows.append(("admission", instance.fee_admission, "Admission fee"))
    if getattr(instance, "add_tuition", False) and (instance.fee_tuition or 0) > 0:
        rows.append(("tuition", instance.fee_tuition, "First month tuition"))
    if getattr(instance, "add_bus", False) and (instance.fee_bus or 0) > 0:
        rows.append(("bus", instance.fee_bus, "Bus service"))
    if getattr(instance, "add_exam", False) and (instance.fee_exam or 0) > 0:
        rows.append(("exam", instance.fee_exam, "Exam fee"))  # ✅ correct category

    paid_date = instance.paid_at.date() if getattr(instance, "paid_at", None) else timezone.localdate()
    for code, amount, label in rows:
        Income.objects.create(
            category=_income_cat(code, label),
            amount=amount,
            date=paid_date,
            description=f"{label} — {instance.full_name} | {tag or 'TXN:n/a'}",
            # NOTE: no content_object unless Income has a GenericForeignKey
        )






def _stripe_enabled():
    return bool(getattr(settings, "STRIPE_SECRET_KEY", ""))

def _is_staff(u): return u.is_authenticated and u.is_staff

@login_required
def stripe_checkout_create(request, invoice_id: int):
    invoice = get_object_or_404(TuitionInvoice, pk=invoice_id)

    # allow if the invoice belongs to the logged-in student
    if invoice.student_id != request.user.id:
        return HttpResponseForbidden("Not allowed.")

    if not _stripe_enabled():
        messages.error(request, "Stripe keys not configured.")
        return redirect("finance-overview")

    invoice = get_object_or_404(TuitionInvoice, pk=invoice_id)
    balance = (invoice.tuition_amount or decimal.Decimal("0")) - (invoice.paid_amount or decimal.Decimal("0"))
    if balance <= 0:
        messages.info(request, "This invoice has no outstanding balance.")
        return redirect("finance-overview")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # amount in cents
    amount_cents = int((balance.quantize(decimal.Decimal("0.01")) * 100).to_integral_value())

    # We’ll store invoice_id in metadata to reconcile at webhook time.
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": settings.STRIPE_CURRENCY,
                "product_data": {"name": f"Tuition {invoice.period_year}-{invoice.period_month:02d} ({invoice.student})"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        metadata={"invoice_id": str(invoice.id)},
        success_url=f"{settings.SITE_URL}{reverse('content:stripe-checkout-success')}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.SITE_URL}{reverse('content:stripe-checkout-cancel')}",
    )

    # Redirect staff/admin straight to hosted checkout
    return redirect(session.url)

@login_required
def stripe_checkout_success(request):
    messages.success(request, "Payment processing… If successful, it will appear on the invoice within a few seconds.")
    return redirect("finance-overview")

@login_required
def stripe_checkout_cancel(request):
    messages.info(request, "Payment cancelled.")
    return redirect("finance-overview")


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return HttpResponseBadRequest(str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        metadata = session.get("metadata") or {}
        user_id = metadata.get("user_id")
        kind    = metadata.get("kind", "")

        # Amount actually paid (in cents). Prefer amount_total on session.
        amount_cents = session.get("amount_total") or 0
        amount = Decimal(amount_cents) / Decimal("100")

        # Stripe payment intent id (stable identifier for txn)
        txn_id = session.get("payment_intent") or session.get("id")

        # Safety: make sure user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse("user not found", status=200)

        if kind == "bulk":
            # Fan out across unpaid invoices (FIFO)
            allocate_payment_across_invoices(
                user=user,
                amount=amount,
                provider="stripe",
                txn_id=str(txn_id),
            )
        else:
            # keep your existing single-invoice branch here (unchanged)
            # e.g., read metadata["invoice_id"] and mark just that one.
            pass

    return HttpResponse(status=200)
@require_GET
def receipt_by_txn(request, txn_id: str):
    """
    Redirects to the PDF for the first PaymentReceipt that matches this txn_id.
    Useful for templates where we only have the payment.txn_id handy.
    """
    rec = PaymentReceipt.objects.filter(txn_id=txn_id).order_by("-id").first()
    if not rec or not rec.pdf:
        raise Http404("Receipt not found")
    return redirect(rec.pdf.url)


# ============== LIST (self-service page) ==============
@login_required
def my_invoices(request):
    # ensure current + next exist (or remove if you don’t want auto-create)
    ensure_monthly_window_for_user(request.user, months_ahead=1)

    zero = Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2))

    invoices = (
        TuitionInvoice.objects
        .filter(student=request.user)
        .order_by("-period_year", "-period_month", "-id")
        .annotate(
            display_balance=ExpressionWrapper(
                Coalesce(F("tuition_amount"), zero) - Coalesce(F("paid_amount"), zero),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
    )

    summary = compute_dues_summary(request.user)
    return render(request, "students/invoices.html", {"invoices": invoices, "summary": summary})

# ============== PAY ONE INVOICE ==============
@login_required
def invoice_pay(request: HttpRequest, invoice_id: int):
    """
    Create a Stripe Checkout Session for a single invoice’s remaining balance.
    """
    inv = get_object_or_404(TuitionInvoice, pk=invoice_id, student=request.user)
    balance = (inv.tuition_amount or decimal.Decimal("0")) - (inv.paid_amount or decimal.Decimal("0"))
    if balance <= 0:
        messages.info(request, "This invoice is already fully paid.")
        return redirect("my-invoices")

    amount_cents = int((balance.quantize(decimal.Decimal("0.01")) * 100).to_integral_value())

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": settings.STRIPE_CURRENCY,
                "product_data": {"name": f"Tuition {inv.period_year}-{inv.period_month:02d}"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        metadata={
            "kind": "single",
            "invoice_id": str(inv.id),
            "student_id": str(request.user.id),
        },
        success_url=f"{settings.SITE_URL}{reverse('my-invoices')}?paid=1",
        cancel_url=f"{settings.SITE_URL}{reverse('my-invoices')}?cancel=1",
    )
    return redirect(session.url, permanent=False)


# ============== BULK PAY: ALL DUES (single line item) ==============
@login_required
def invoice_bulk_checkout_all(request: HttpRequest):
    """
    POST only. Send the student to Stripe for the sum of ALL unpaid invoices.
    One line item; webhook should allocate FIFO using `allocate_payment_across_invoices`.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    summary = compute_dues_summary(request.user)
    total_due = summary.total_due or Decimal("0")
    if total_due <= 0:
        messages.info(request, "You have no dues to pay.")
        return redirect("my-invoices")

    amount_cents = int((total_due * Decimal("100")).to_integral_value())

    # Optional metadata: list unpaid invoice IDs
    invoice_ids_csv = ",".join(str(i.id) for i in summary.unpaid)

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": settings.STRIPE_CURRENCY,
                "product_data": {"name": "Pay all outstanding school fees"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        metadata={
            "kind": "bulk_all",
            "user_id": str(request.user.id),
            "invoice_ids": invoice_ids_csv,
        },
        success_url=f"{settings.SITE_URL}{reverse('my-invoices')}?paid=1",
        cancel_url=f"{settings.SITE_URL}{reverse('my-invoices')}?cancel=1",
    )
    return redirect(session.url, permanent=False)


# ============== BULK PAY: SELECTED INVOICES (multiple line items) ==============
@login_required
def invoice_bulk_checkout_selected(request: HttpRequest):
    """
    POST JSON: { "invoice_ids": [1,2,3] }
    Creates a Stripe Checkout Session with multiple line items for each invoice's **balance**.
    Returns JSON: {"ok": true, "url": "..."} to redirect on the client side.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = {}

    ids = payload.get("invoice_ids") or []
    if not isinstance(ids, list) or not ids:
        return JsonResponse({"ok": False, "error": "no_invoices"}, status=400)

    qs = (
        TuitionInvoice.objects
        .filter(student=request.user, id__in=ids)
        .order_by("period_year", "period_month", "id")
    )
    if not qs.exists():
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)

    currency = getattr(settings, "STRIPE_CURRENCY", "usd")
    line_items = []
    for inv in qs:
        balance = (inv.tuition_amount or Decimal("0")) - (inv.paid_amount or Decimal("0"))
        if balance <= 0:
            continue
        amount_cents = int((balance.quantize(Decimal("0.01")) * 100).to_integral_value())
        line_items.append({
            "price_data": {
                "currency": currency,
                "product_data": {
                    "name": f"Tuition {inv.period_year}-{inv.period_month:02d}",
                },
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        })

    if not line_items:
        return JsonResponse({"ok": False, "error": "no_positive_balances"}, status=400)

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=line_items,
        metadata={
            "kind": "bulk_selected",
            "user_id": str(request.user.id),
            "invoice_ids": ",".join(map(str, ids)),
        },
        success_url=f"{settings.SITE_URL}{reverse('my-invoices')}?paid=1",
        cancel_url=f"{settings.SITE_URL}{reverse('my-invoices')}?cancel=1",
    )
    return JsonResponse({"ok": True, "url": session.url})


@login_required
def invoice_bulk_checkout(request):
    """
    Backend-first: charge the user's *total due* by allocating across unpaid
    invoices (oldest → newest). Swap this later to Stripe if you want.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    summary = compute_dues_summary(request.user)
    total_due = Decimal(summary.total_due or 0)

    if total_due <= 0:
        messages.info(request, "You have no dues to pay.")
        return redirect("my-invoices")

    # Allocate like a successful payment:
    allocate_payment_across_invoices(
        request.user,
        amount=total_due,
        provider="manual",
        txn_id=None,
    )
    messages.success(request, f"Paid all dues (৳ {total_due}). Thank you!")
    return redirect("my-invoices")
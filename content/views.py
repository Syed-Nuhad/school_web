# content/views.py
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic import DetailView, CreateView

from .forms import AdmissionApplicationForm
from decimal import Decimal
from typing import Dict

from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone

from .decorators import teacher_or_admin_required
from .models import Banner, Notice, TimelineEvent, Course, AdmissionApplication
import json, uuid, requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.urls import reverse

P = settings.PAYMENTS

# ---------- helpers ----------
def _image_src(file_field, fallback_url: str | None) -> str:
    """Prefer uploaded file URL; otherwise use the provided external URL; else empty."""
    if file_field:
        try:
            return file_field.url
        except Exception:
            pass
    return (fallback_url or "").strip()


# ---------- PUBLIC READ (for your frontend) ----------

@require_GET
def api_slides(request):
    """
    Kept name 'api_slides' for compatibility, but actually serves Banner data.
    """
    items = Banner.objects.filter(is_active=True).order_by("order", "-created_at")
    data = []
    for b in items:
        data.append({
            "id": b.id,
            "title": b.title,
            # map your old 'caption' field name to the actual 'subtitle' in Banner
            "caption": b.subtitle,
            "subtitle": b.subtitle,
            "image": _image_src(b.image, b.image_url),
            "order": b.order,
            "button_text": b.button_text,
            "button_link": b.button_link,
        })
    return JsonResponse({"items": data})


@require_GET
def api_notices(request):
    """
    Optional ?limit=3 to restrict number of notices for homepage.
    """
    qs = Notice.objects.filter(is_active=True)

    try:
        limit = int(request.GET.get("limit", "0"))
    except ValueError:
        limit = 0

    qs = qs.order_by("-published_at", "-created_at")
    if limit > 0:
        qs = qs[:limit]

    data = []
    for n in qs:
        data.append({
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "image": _image_src(n.image, n.image_url),
            "link_url": (n.link_url or "").strip(),
            # extra context for UI if you want it:
            "grade": (n.grade or "").strip() if hasattr(n, "grade") else "",
            "section": (n.section or "").strip() if hasattr(n, "section") else "",
            "posted_by": (n.posted_by.username if getattr(n, "posted_by", None) else None),
        })
    return JsonResponse({"items": data})


@require_GET
def api_timeline(request):
    # first 3 timeline items for homepage
    qs = TimelineEvent.objects.filter(is_active=True).order_by("date", "order")[:3]
    data = []
    for e in qs:
        data.append({
            "id": e.id,
            "title": e.title,
            "date": e.date.isoformat(),
            "description": e.description,
            "order": e.order,
        })
    return JsonResponse({"items": data})


# ---------- TEACHER/ADMIN MANAGE (backend only) ----------

@teacher_or_admin_required
@require_POST
def manage_slide_create(request):
    """
    Kept function name for compatibility; creates a Banner.
    Accepts:
      - title (str)
      - subtitle OR caption (str)
      - image (file) OR image_url (str)
      - order (int)
      - button_text (str, optional)
      - button_link (str, optional)
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
    Accepts:
      - title (required)
      - body, link_url, image(file) or image_url
      - grade, section (optional – if your model has them)
      - published_at (ISO datetime '2025-08-05T10:00:00' or date '2025-08-05')
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
    published_at = None
    if published_raw:
        published_at = parse_datetime(published_raw) or parse_date(published_raw)

    n = Notice(
        title=title,
        body=body,
        link_url=link_url,
        image_url=image_url,
        posted_by=request.user,  # IMPORTANT: use posted_by (teacher/admin)
    )

    # Only set grade/section if your model has these fields
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

    # default publish time if not provided
    if not n.published_at:
        n.published_at = timezone.now()

    n.save()
    return JsonResponse({"created": {"id": n.id}}, status=201)


@teacher_or_admin_required
@require_POST
def manage_timeline_create(request):
    """
    Creates a TimelineEvent.
    Accepts:
      - title (required)
      - date (YYYY-MM-DD, required)
      - description, order
    """
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    date_raw = (request.POST.get("date") or "").strip()  # YYYY-MM-DD

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


def _json_bad(msg, code=400): return JsonResponse({"ok": False, "error": msg}, status=code)
def _json_ok(**k): return JsonResponse({"ok": True, **k})

# ---------- PayPal: create → capture ----------
def _pp_token():
    r = requests.post(f"{P['PP_BASE']}/v1/oauth2/token",
                      auth=(P["PP_CLIENT"], P["PP_SECRET"]),
                      data={"grant_type":"client_credentials"},
                      timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

@csrf_exempt
def paypal_create(request):
    if request.method != "POST": return HttpResponseBadRequest("POST only")
    try: data = json.loads(request.body or "{}")
    except: data = {}
    amount = float(data.get("amount") or 0) or 15.00
    currency = data.get("currency") or "USD"

    try:
        token = _pp_token()
        order = {
            "intent": "CAPTURE",
            "purchase_units": [{
              "reference_id": f"ADM_{uuid.uuid4().hex[:10]}",
              "amount": {"currency_code": currency, "value": f"{amount:.2f}"}
            }]
        }
        r = requests.post(f"{P['PP_BASE']}/v2/checkout/orders",
                          headers={"Content-Type":"application/json",
                                   "Authorization": f"Bearer {token}"},
                          json=order, timeout=20)
        r.raise_for_status()
        j = r.json()
        return _json_ok(orderID=j["id"])
    except Exception as e:
        return _json_bad(str(e), 502)

@csrf_exempt
def paypal_capture(request):
    if request.method != "POST": return HttpResponseBadRequest("POST only")
    try: body = json.loads(request.body or "{}")
    except: body = {}
    order_id = body.get("orderID")
    if not order_id: return _json_bad("Missing orderID")

    try:
        token = _pp_token()
        r = requests.post(f"{P['PP_BASE']}/v2/checkout/orders/{order_id}/capture",
                          headers={"Content-Type":"application/json",
                                   "Authorization": f"Bearer {token}"},
                          timeout=20)
        r.raise_for_status()
        j = r.json()
        # check final status
        paid = (j.get("status") == "COMPLETED")
        return _json_ok(paid=paid, details=j)
    except Exception as e:
        return _json_bad(str(e), 502)












def compute_fee(course: Course, *, add_bus: bool, add_hostel: bool, add_marksheet: bool) -> Dict[str, Decimal]:
    """
    Returns a dict with individual items and the grand total.
    Every value is Decimal; never None.
    """
    fee_admission = course.admission_fee or Decimal("0.00")
    fee_tuition   = course.first_month_tuition or Decimal("0.00")
    fee_exam      = course.exam_fee or Decimal("0.00")

    fee_bus       = (course.bus_fee or Decimal("0.00")) if add_bus else Decimal("0.00")
    fee_hostel    = (course.hostel_fee or Decimal("0.00")) if add_hostel else Decimal("0.00")
    fee_marksheet = (course.marksheet_fee or Decimal("0.00")) if add_marksheet else Decimal("0.00")

    fee_total = fee_admission + fee_tuition + fee_exam + fee_bus + fee_hostel + fee_marksheet

    return {
        "fee_admission": fee_admission,
        "fee_tuition": fee_tuition,
        "fee_exam": fee_exam,
        "fee_bus": fee_bus,
        "fee_hostel": fee_hostel,
        "fee_marksheet": fee_marksheet,
        "fee_total": fee_total,
    }



def send_payment_success_email(application):
    if not application.email:
        return
    subject = "Payment Successful – Your Admission Application"
    amount  = application.fee_selected_total or application.fee_total
    lines = [
        f"Dear {application.full_name},",
        "",
        "We have received your payment successfully.",
        f"Course: {application.desired_course}",
        f"Amount: ৳ {amount:,.2f}",
        f"Transaction ID: {application.payment_txn_id or 'N/A'}",
        "",
        "Thank you.",
    ]
    body = "\n".join(lines)
    send_mail(
        subject,
        body,
        getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        [application.email],
        fail_silently=True,
    )






class AdmissionReviewView(DetailView):
    model = AdmissionApplication
    template_name = "admissions/review.html"
    context_object_name = "application"



# Apply (creates a draft application + fee snapshot in form_valid)
class AdmissionApplyView(CreateView):
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
        app = form.save(commit=False)
        course = app.desired_course

        # snapshot base fees from course
        app.fee_admission = course.admission_fee or Decimal("0")
        app.fee_tuition   = course.first_month_tuition or Decimal("0")
        app.fee_exam      = course.exam_fee or Decimal("0")

        # add-ons selected by user (booleans in the form)
        app.fee_bus       = course.bus_fee if app.add_bus else Decimal("0")
        app.fee_hostel    = course.hostel_fee if app.add_hostel else Decimal("0")
        app.fee_marksheet = course.marksheet_fee if app.add_marksheet else Decimal("0")

        app.fee_total = (
            app.fee_admission + app.fee_tuition + app.fee_exam +
            app.fee_bus + app.fee_hostel + app.fee_marksheet
        )

        # not paid yet
        app.payment_status = "pending"
        app.save()
        return redirect("admissions:review", pk=app.pk)



# Confirm (marks as paid for now; later you’ll swap in real bKash/PayPal)
class AdmissionConfirmView(DetailView):
    model = AdmissionApplication
    template_name = "admissions/confirm.html"
    context_object_name = "application"

    def post(self, request, *args, **kwargs):
        app = self.get_object()

        # TODO: replace this block with real gateway verification result
        app.payment_status = "paid"
        app.payment_method = request.POST.get("method", "manual")
        app.payment_reference = request.POST.get("reference", "")
        app.save()

        # email receipt
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

# Receipt (print/PDF-friendly)
class AdmissionReceiptView(DetailView):
    model = AdmissionApplication
    template_name = "admissions/receipt.html"
    context_object_name = "application"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Optional institution info for the template header
        ctx.update({
            "institution_name": getattr(settings, "INSTITUTION_NAME", "Your Institution"),
            "institution_phone": getattr(settings, "INSTITUTION_PHONE", None),
            "institution_email": getattr(settings, "INSTITUTION_EMAIL", None),
            "institution_address": getattr(settings, "INSTITUTION_ADDRESS", None),
            "institution_logo_url": getattr(settings, "INSTITUTION_LOGO_URL", None),
        })
        return ctx


def _amount_for(app: AdmissionApplication) -> Decimal:
    # you already computed and stored this on submit
    return app.fee_selected_total or app.fee_total or Decimal("0")

@require_GET
def create_payment_order(request, pk: int):
    """
    Returns the exact server-computed amount that must be charged.
    Your front-end payment button should read this amount and create a gateway order.
    """
    app = get_object_or_404(AdmissionApplication, pk=pk)
    if app.payment_status == "paid":
        return JsonResponse({"error": "already_paid"}, status=400)

    amount = _amount_for(app)
    return JsonResponse({
        "application_id": app.pk,
        "amount": str(amount),               # keep as string for JS safety
        "currency": "BDT",
        "description": f"Admission fees for {app.full_name}",
    })

@csrf_exempt
@require_POST
def mark_payment_paid(request, pk: int):
    """
    Call this AFTER your gateway confirms a successful capture.
    Body JSON: { "provider": "paypal"|"bkash", "transaction_id": "..." }
    """
    import json
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = {}

    provider = (data.get("provider") or "").lower()
    txn_id   = data.get("transaction_id") or ""

    if provider not in {"paypal", "bkash", "card", "visa", "mastercard"}:
        return JsonResponse({"error": "invalid_provider"}, status=400)
    if not txn_id:
        return JsonResponse({"error": "missing_transaction_id"}, status=400)

    app = get_object_or_404(AdmissionApplication, pk=pk)
    if app.payment_status == "paid":
        return JsonResponse({"status": "already_paid"})

    # (Optional) you can verify amount again right here or verify via gateway API/IPN.

    app.mark_paid(provider, txn_id)
    send_payment_success_email(app)
    return JsonResponse({"status": "ok"})
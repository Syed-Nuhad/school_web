# content/views.py
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone

from .decorators import teacher_or_admin_required
from .models import Banner, Notice, TimelineEvent
import json, uuid, requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
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

# ---------- bKash: token → create → (redirect) → execute ----------
def _bkash_grant():
    r = requests.post(f"{P['BKASH_BASE']}/checkout/token/grant",
                      headers={"Content-Type":"application/json",
                               "username":P["BKASH_USERNAME"],
                               "password":P["BKASH_PASSWORD"]},
                      json={"app_key":P["BKASH_APP_KEY"],
                            "app_secret":P["BKASH_APP_SECRET"]},
                      timeout=20)
    r.raise_for_status()
    return r.json()["id_token"]

@csrf_exempt
def bkash_init(request):
    if request.method != "POST": return HttpResponseBadRequest("POST only")
    try: data = json.loads(request.body or "{}")
    except: data = {}
    amount = float(data.get("amount") or 0) or 1500.0

    try:
        token = _bkash_grant()
        payload = {
            "mode": "0011",
            "payerReference": "ADMISSION",
            "callbackURL": f"{P['SITE_ORIGIN']}{reverse('bkash_return')}",
            "amount": f"{amount:.2f}",
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": f"ADM_{uuid.uuid4().hex[:10]}",
        }
        cr = requests.post(f"{P['BKASH_BASE']}/checkout/payment/create",
                           headers={"Content-Type":"application/json",
                                    "authorization": token,
                                    "x-app-key": P["BKASH_APP_KEY"]},
                           json=payload, timeout=20)
        cr.raise_for_status()
        j = cr.json()
        url = j.get("bkashURL")
        if not url: return _json_bad("bKash did not return bkashURL", 502)
        # Store paymentID in session if you want (for your own linking/reconcile)
        request.session["bkash_payment_id"] = j.get("paymentID")
        return _json_ok(bkash_url=url)
    except Exception as e:
        return _json_bad(str(e), 502)

def bkash_return(request):
    """User returns from bKash. Execute and redirect back to form with ?paid=1/0."""
    payment_id = request.GET.get("paymentID") or request.session.get("bkash_payment_id")
    if not payment_id:
        return HttpResponseRedirect("/admissions/apply/?paid=0")
    try:
        token = _bkash_grant()
        ex = requests.post(f"{P['BKASH_BASE']}/checkout/payment/execute/{payment_id}",
                           headers={"Content-Type":"application/json",
                                    "authorization": token,
                                    "x-app-key": P["BKASH_APP_KEY"]},
                           timeout=20)
        ex.raise_for_status()
        j = ex.json()
        status = str(j.get("transactionStatus","")).lower()
        paid = status in ("completed","completedsuccess","success","validated","valid")
        return HttpResponseRedirect(f"/admissions/apply/?paid={'1' if paid else '0'}")
    except Exception:
        return HttpResponseRedirect("/admissions/apply/?paid=0")

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

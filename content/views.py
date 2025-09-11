# content/views.py
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone

from .decorators import teacher_or_admin_required
from .models import Banner, Notice, TimelineEvent


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

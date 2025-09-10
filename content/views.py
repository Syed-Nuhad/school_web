from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_datetime, parse_date
from django.conf import settings

from .decorators import teacher_or_admin_required
from .models import Slide, Notice, TimelineEvent


# ---------- PUBLIC READ (for your frontend) ----------

@require_GET
def api_slides(request):
    items = Slide.objects.filter(is_active=True).order_by("order", "-created_at")
    data = []
    for s in items:
        data.append({
            "id": s.id,
            "title": s.title,
            "caption": s.caption,
            "image": s.image.url if s.image else "",
            "image_url": s.image_url,
            "order": s.order,
        })
    return JsonResponse({"items": data})


@require_GET
def api_notices(request):
    qs = Notice.objects.filter(is_active=True)
    # optional ?limit=3 for the first three on the homepage
    try:
        limit = int(request.GET.get("limit", "0"))
    except ValueError:
        limit = 0
    if limit > 0:
        qs = qs.order_by("-published_at", "-created_at")[:limit]
    else:
        qs = qs.order_by("-published_at", "-created_at")

    data = []
    for n in qs:
        data.append({
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "image": n.image.url if n.image else "",
            "image_url": n.image_url,
            "link_url": n.link_url,
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
    title = (request.POST.get("title") or "").strip()
    caption = (request.POST.get("caption") or "").strip()
    image_url = (request.POST.get("image_url") or "").strip()
    order = int(request.POST.get("order") or 0)

    if not title and not image_url and "image" not in request.FILES:
        return HttpResponseBadRequest("Provide at least a title and an image or image_url.")

    s = Slide(
        title=title,
        caption=caption,
        image_url=image_url,
        order=order,
        created_by=request.user,
    )
    if "image" in request.FILES:
        s.image = request.FILES["image"]
    s.save()
    return JsonResponse({"created": {"id": s.id}}, status=201)


@teacher_or_admin_required
@require_POST
def manage_notice_create(request):
    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    link_url = (request.POST.get("link_url") or "").strip()
    image_url = (request.POST.get("image_url") or "").strip()

    # allow published_at or default to now
    published_raw = (request.POST.get("published_at") or "").strip()
    published_at = None
    if published_raw:
        # accepts ISO "2025-08-05T10:00:00" or just date "2025-08-05"
        published_at = parse_datetime(published_raw) or parse_date(published_raw)

    if not title:
        return HttpResponseBadRequest("title is required")

    n = Notice(
        title=title,
        body=body,
        link_url=link_url,
        image_url=image_url,
        created_by=request.user,
    )
    if hasattr(published_at, "isoformat"):  # datetime
        n.published_at = published_at
    elif published_at:  # date
        from datetime import datetime
        n.published_at = datetime.combine(published_at, datetime.min.time())

    if "image" in request.FILES:
        n.image = request.FILES["image"]

    n.save()
    return JsonResponse({"created": {"id": n.id}}, status=201)


@teacher_or_admin_required
@require_POST
def manage_timeline_create(request):
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    date_raw = (request.POST.get("date") or "").strip()  # YYYY-MM-DD
    order = int(request.POST.get("order") or 0)

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

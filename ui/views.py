from __future__ import annotations

from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from content.models import Banner, Notice

def home(request):
    banners_qs = (
        Banner.objects
        .filter(is_active=True)
        .filter(Q(image__isnull=False) | ~Q(image_url=""))   # only banners with an image source
        .order_by("order", "-created_at")
    )
    notices_qs = (
        Notice.objects.filter(is_active=True)
        .order_by("-published_at", "-created_at")[:6]
    )

    context = {
        "banners": banners_qs,
        "banners_flat": [{
            "title": b.title,
            "subtitle": b.subtitle,
            "image": b.image_src,
            "button_text": b.button_text,
            "button_link": b.button_link,
            "order": b.order,
        } for b in banners_qs],
        "notices": notices_qs,
        "notices_flat": [{
            "title": n.title,
            "subtitle": n.subtitle,
            "image": n.image_src,
            "published_at": n.published_at,
            "url": reverse("notice_detail", args=[n.pk]),
        } for n in notices_qs],
    }
    return render(request, "index.html", context)

def notices_list(request):
    """
    Paginated list of active notices.
    """
    qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")
    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page") or 1
    try:
        notices = paginator.get_page(page_number)
    except EmptyPage:
        notices = paginator.get_page(paginator.num_pages)

    return render(request, "notices/notice_list.html", {"notices": notices})


def notice_detail(request, pk: int):
    """
    Detail page for a single notice + right-rail 'More notices'.
    """
    # NOTE: No select_related('posted_by') because model has no such FK now.
    notice = get_object_or_404(
        Notice.objects.filter(is_active=True),
        pk=pk,
    )

    more_notices = (
        Notice.objects.filter(is_active=True)
        .exclude(pk=notice.pk)
        .order_by("-published_at", "-created_at")[:8]
    )

    return render(
        request,
        "notice_detail.html",
        {"notice": notice, "more_notices": more_notices},
    )
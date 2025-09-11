from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, get_object_or_404
# Create your views here.

# ui/views.py
from django.shortcuts import render
from content.models import Banner, Notice


def home(request):
    banners_qs = Banner.objects.filter(is_active=True).order_by("order", "-created_at")
    notices_qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")[:6]

    context = {
        "banners": banners_qs,
        "banners_flat": [
            {
                "title": b.title,
                "subtitle": b.subtitle,
                "image": b.image_src,
                "button_text": b.button_text,
                "button_link": b.button_link,
                "order": b.order,
            } for b in banners_qs
        ],
        "notices": notices_qs,
        "notices_flat": [
            {
                "title": n.title,
                "subtitle": n.subtitle,
                "image": n.image_src,
                "published_at": n.published_at,
                "url": n.url,            # <- key part
            } for n in notices_qs
        ],
    }
    return render(request, "index.html", context)


def notices_list(request):
    qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")
    paginator = Paginator(qs, 12)
    notices = paginator.get_page(request.GET.get("page"))
    return render(request, "notices/notice_list.html", {"notices": notices})


def notice_detail(request, pk: int):
    notice = get_object_or_404(Notice.objects.select_related("posted_by"), pk=pk, is_active=True)
    more_notices = (
        Notice.objects.filter(is_active=True)
        .exclude(pk=notice.pk)
        .order_by("-published_at", "-created_at")[:8]
    )
    return render(request, "notices/notice_detail.html", {
        "notice": notice,
        "more_notices": more_notices,
    })


# ui/views.py


def notice_detail(request, pk: int):
    """
    Detail page for a notice.
    - Shows the selected notice
    - Provides 'Up next' (other recent notices) for the right sidebar
    """
    notice = get_object_or_404(
        Notice.objects.select_related("posted_by"),
        pk=pk,
        is_active=True,
    )

    # Right-rail: show up to 8 other recent notices
    more_notices = (
        Notice.objects.filter(is_active=True)
        .exclude(pk=notice.pk)
        .order_by("-published_at", "-created_at")[:8]
    )

    ctx = {
        "notice": notice,
        "more_notices": more_notices,
    }
    return render(request, "notices/notice_detail.html", ctx)


def notices_list(request):
    """
    Simple list index so the 'Back to Notices' link works.
    (Feel free to style this later.)
    """
    qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")
    paginator = Paginator(qs, 12)
    page = request.GET.get("page")
    notices = paginator.get_page(page)
    return render(request, "notices/notice_list.html", {"notices": notices})
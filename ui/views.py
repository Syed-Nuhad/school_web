# ui/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from content.models import Banner, Notice


def home(request):
    """
    Render index.html with dynamic banners and the latest notices.
    - Banners: active, ordered by 'order' then newest
    - Notices: latest 6 active
    """
    banners = Banner.objects.filter(is_active=True).order_by("order", "-created_at")
    notices = (
        Notice.objects.filter(is_active=True)
        .order_by("-published_at", "-created_at")[:6]
    )

    return render(request, "index.html", {
        "banners": banners,
        "notices": notices,
    })


def notices_list(request):
    """
    Paginated list of active notices for the notices index page.
    """
    qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "notices/notice_list.html", {
        "notices": page_obj,   # template iterates over page_obj
    })


def notice_detail(request, pk: int):
    """
    Detail page for a single notice + a right-rail list of other recent notices.
    """
    notice = get_object_or_404(
        Notice.objects.select_related("posted_by"),
        pk=pk, is_active=True
    )
    more_notices = (
        Notice.objects.filter(is_active=True)
        .exclude(pk=notice.pk)
        .order_by("-published_at", "-created_at")[:8]
    )

    return render(request, "notices/notice_detail.html", {
        "notice": notice,
        "more_notices": more_notices,
    })

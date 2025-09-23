from __future__ import annotations

from django.shortcuts import get_object_or_404

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.apps import apps
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage, send_mail

from content.models import (
    Banner, Notice, TimelineEvent, GalleryItem, AboutSection,
    AcademicCalendarItem, Course, FunctionHighlight, CollegeFestival, ContactInfo, FooterSettings, GalleryPost
)
from content.forms import ContactForm


def _paginate(request, queryset, param_name: str, per_page: int):
    """Small helper to DRY pagination."""
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get(param_name) or 1
    try:
        page = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)

    cur = page.number
    total = paginator.num_pages
    # compact window like: current-1 .. current .. current+1
    start = max(cur - 1, 1)
    end = min(cur + 1, total)
    page_range = range(start, end + 1)
    return page, page_range, paginator


# ui/views.py





def home(request):
    # --- Core queries ---
    banners_qs = (
        Banner.objects
        .filter(is_active=True)
        .filter(Q(image__isnull=False) | ~Q(image_url=""))
        .order_by("order", "-created_at")
    )
    notices_qs = (
        Notice.objects
        .filter(is_active=True)
        .order_by("-published_at", "-created_at")[:4]  # ← only 4
    )
    timeline_qs  = TimelineEvent.objects.filter(is_active=True).order_by("date", "order")[:4]
    gallery_qs   = GalleryItem.objects.filter(is_active=True)
    about        = AboutSection.objects.filter(is_active=True).order_by("order").first()
    calendar_items = AcademicCalendarItem.objects.filter(is_active=True).order_by("order")
    courses      = Course.objects.filter(is_active=True).order_by("order", "title")

    # Contact block + blank form
    contact_info = ContactInfo.objects.filter(is_active=True).order_by("-updated_at").first()
    contact_form = ContactForm()

    # Function Highlights (paginate: 3 per page)
    functions_qs = FunctionHighlight.objects.filter(is_active=True).order_by("order", "-id")
    functions_page, functions_page_range, _ = _paginate(request, functions_qs, "fpage", per_page=3)

    # College Festivals (paginate: default 2 per page; allow override via ?fest_per_page=)
    try:
        fest_per_page = int(request.GET.get("fest_per_page", 2))
    except ValueError:
        fest_per_page = 2
    festivals_qs = CollegeFestival.objects.filter(is_active=True).prefetch_related("media_items").order_by("order", "-created_at")
    festivals_page, festivals_page_range, _ = _paginate(request, festivals_qs, "festpage", per_page=fest_per_page)

    # Members (counts + items)
    Member = apps.get_model("content", "Member", require_ready=False)
    member_sections = [
        {"key": "hod",     "label": "Head of Department", "items": []},
        {"key": "teacher", "label": "Teachers",           "items": []},
        {"key": "student", "label": "Students",           "items": []},
        {"key": "staff",   "label": "Staff",              "items": []},
    ]
    members_counts = {"hod": 0, "teacher": 0, "student": 0, "staff": 0}
    if Member:
        for sec in member_sections:
            qs = Member.objects.filter(role=sec["key"], is_active=True).order_by("order", "name")
            sec["items"] = list(qs)
            members_counts[sec["key"]] = qs.count()
    footer = FooterSettings.objects.filter(is_active=True).order_by("-updated_at", "-id").first()

    context = {
        "banners": banners_qs,
        "gallery_items": gallery_qs,
        "about": about,
        "calendar_items": calendar_items,
        "courses": courses,

        "banners_flat": [{
            "title": b.title, "subtitle": b.subtitle, "image": getattr(b, "image_src", None),
            "button_text": b.button_text, "button_link": b.button_link, "order": b.order,
        } for b in banners_qs],

        "notices": notices_qs,
        "notices_flat": [{
            "title": n.title, "subtitle": n.subtitle, "image": getattr(n, "image_src", None),
            "published_at": n.published_at, "url": reverse("notice_detail", args=[n.pk]),
        } for n in notices_qs],

        "timeline_events": timeline_qs,

        # Function Highlights
        "functions": functions_qs,
        "functions_page": functions_page,
        "functions_page_range": functions_page_range,

        # College Festivals
        "festivals": festivals_qs,
        "festivals_page": festivals_page,
        "festivals_page_range": festivals_page_range,

        # Members
        "member_sections": member_sections,
        "members_counts": members_counts,

        # Contact
        "contact_info": contact_info,
        "contact_form": contact_form,
        "footer": footer,
    }
    return render(request, "index.html", context)









def contact_submit(request):
    """
    Saves the contact message and sends:
      1) Notification email to site inbox (DEFAULT_CONTACT_EMAIL or DEFAULT_FROM_EMAIL)
      2) Auto-acknowledgement email to the sender
    Then redirects back to #contact with a flash message.
    """
    if request.method != "POST":
        return redirect(reverse("home") + "#contact")

    form = ContactForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please fix the errors below.")
        # Re-render the full home with the bound form + contact info (so errors show)
        contact_info = ContactInfo.objects.filter(is_active=True).order_by("-updated_at").first()
        return render(request, "index.html", {
            "contact_info": contact_info,
            "contact_form": form,
        })

    msg = form.save()  # ContactMessage row

    # ---------- build email data ----------
    site_inbox = getattr(settings, "DEFAULT_CONTACT_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    from_addr  = getattr(settings, "DEFAULT_FROM_EMAIL", getattr(settings, "EMAIL_HOST_USER", None))

    subject_admin = f"[Website] New Contact: {msg.subject}"
    body_admin = (
        f"New contact message received:\n\n"
        f"Name: {msg.name}\n"
        f"Email: {msg.email}\n"
        f"Phone: {msg.phone or '-'}\n"
        f"Sent: {msg.created_at:%Y-%m-%d %H:%M}\n\n"
        f"Message:\n{msg.message}\n"
    )

    subject_user = "Thanks for contacting us"
    body_user = (
        f"Hi {msg.name},\n\n"
        f"Thanks for reaching out. We received your message:\n\n"
        f"Subject: {msg.subject}\n"
        f"Message:\n{msg.message}\n\n"
        f"We'll get back to you soon.\n\n"
        f"Best regards,\n"
        f"{getattr(settings, 'SITE_NAME', 'Our College')}"
    )

    # ---------- send emails (safe but real) ----------
    admin_ok = False
    user_ok  = False

    if site_inbox and from_addr:
        try:
            # notify site/admin
            email_admin = EmailMessage(
                subject_admin, body_admin, from_addr, [site_inbox],
                headers={"Reply-To": msg.email}
            )
            email_admin.send(fail_silently=False)
            admin_ok = True
        except Exception:
            admin_ok = False

    if from_addr:
        try:
            # auto-ack to sender
            send_mail(
                subject=f"[Website] New message: {msg.subject}",
                message=f"From: {msg.name} <{msg.email}>\n\n{msg.message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_CONTACT_EMAIL],
                fail_silently=False,  # <-- show problems instead of swallowing them
            )
            user_ok = True
        except Exception:
            user_ok = False

    if admin_ok:
        messages.success(request, "Thanks! Your message has been sent.")
    else:
        messages.warning(request, "Message saved. Email delivery appears unavailable right now.")

    return redirect(reverse("home") + "#contact")





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
    notice = get_object_or_404(
        Notice.objects.filter(is_active=True),
        pk=pk,
    )

    # Right-rail “more” list (unchanged)
    more_notices = (
        Notice.objects.filter(is_active=True)
        .exclude(pk=notice.pk)
        .order_by("-published_at", "-created_at")[:8]
    )

    # Neighbor notices for step-by-step nav
    prev_notice = (
        Notice.objects.filter(is_active=True, published_at__gt=notice.published_at)
        .order_by("published_at", "created_at")
        .first()
    )
    next_notice = (
        Notice.objects.filter(is_active=True, published_at__lt=notice.published_at)
        .order_by("-published_at", "-created_at")
        .first()
    )

    return render(
        request,
        "notice_detail.html",
        {
            "notice": notice,
            "more_notices": more_notices,
            "prev_notice": prev_notice,   # ← add
            "next_notice": next_notice,   # ← add
        },
    )






def gallery_page(request):
    qs = GalleryPost.objects.filter(is_active=True).order_by("order", "-created_at")
    paginator = Paginator(qs, 12)   # 12 items per page
    page_number = request.GET.get("page") or 1
    page = paginator.get_page(page_number)

    footer = FooterSettings.objects.filter(is_active=True).order_by("-updated_at").first()

    return render(request, "gallery_list.html", {
        "page": page,
        "footer": footer,
    })

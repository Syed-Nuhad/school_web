from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMessage, send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch, Count, Case, When, IntegerField
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from content.forms import ContactForm
from content.models import (
    Banner, Notice, TimelineEvent, GalleryItem, AboutSection,
    AcademicCalendarItem, Course, FunctionHighlight, CollegeFestival, ContactInfo, FooterSettings, GalleryPost,
    ClassResultSummary, ClassTopper, ExamTerm, AcademicClass, ClassResultSubjectAvg, AttendanceSession, Member
)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _staff(user):
    return user.is_authenticated and user.is_staff

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

def summary_toppers_qs():
    """Keep toppers ordered by rank everywhere."""
    return ClassTopper.objects.order_by("rank", "id")

def _apply_result_filters(qs, request):
    """
    Optional GET filters:
      ?year=2025
      ?term_id=3
      ?class_id=12
      ?name=Class 8
      ?section=A
    """
    year = request.GET.get("year")
    term_id = request.GET.get("term_id")
    class_id = request.GET.get("class_id")
    name = request.GET.get("name")
    section = request.GET.get("section")

    if year:
        qs = qs.filter(term__year=year)
    if term_id:
        qs = qs.filter(term_id=term_id)
    if class_id:
        qs = qs.filter(klass_id=class_id)
    if name:
        qs = qs.filter(klass__name__iexact=name)
    if section:
        qs = qs.filter(klass__section__iexact=section)

    return qs

# -------------------------------------------------------------------
# Public pages
# -------------------------------------------------------------------

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
        .order_by("-published_at", "-created_at")[:4]  # only 4
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
    festivals_qs = (CollegeFestival.objects
                    .filter(is_active=True)
                    .prefetch_related("media_items")
                    .order_by("order", "-created_at"))
    festivals_page, festivals_page_range, _ = _paginate(request, festivals_qs, "festpage", per_page=fest_per_page)

    # Members (counts + items)
    member_sections = [
        {"key": "hod",     "label": "Head of Department", "items": []},
        {"key": "teacher", "label": "Teachers",           "items": []},
        {"key": "student", "label": "Students",           "items": []},
        {"key": "staff",   "label": "Staff",              "items": []},
    ]
    members_counts = {"hod": 0, "teacher": 0, "student": 0, "staff": 0}
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
        contact_info = ContactInfo.objects.filter(is_active=True).order_by("-updated_at").first()
        return render(request, "index.html", {
            "contact_info": contact_info,
            "contact_form": form,
        })

    msg = form.save()  # ContactMessage row

    # Email addresses
    site_inbox = getattr(settings, "DEFAULT_CONTACT_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    from_addr  = getattr(settings, "DEFAULT_FROM_EMAIL", getattr(settings, "EMAIL_HOST_USER", None))

    # Admin notification
    admin_ok = False
    if site_inbox and from_addr:
        subject_admin = f"[Website] New Contact: {msg.subject}"
        body_admin = (
            f"New contact message received:\n\n"
            f"Name: {msg.name}\n"
            f"Email: {msg.email}\n"
            f"Phone: {msg.phone or '-'}\n"
            f"Sent: {msg.created_at:%Y-%m-%d %H:%M}\n\n"
            f"Message:\n{msg.message}\n"
        )
        try:
            email_admin = EmailMessage(
                subject_admin, body_admin, from_addr, [site_inbox],
                headers={"Reply-To": msg.email}
            )
            email_admin.send(fail_silently=False)
            admin_ok = True
        except Exception:
            admin_ok = False

    # Auto-acknowledgement to the sender
    user_ok = False
    if from_addr and msg.email:
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
        try:
            send_mail(
                subject_user,
                body_user,
                from_addr,
                [msg.email],  # send to user
                fail_silently=False,
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
    """Paginated list of active notices."""
    qs = Notice.objects.filter(is_active=True).order_by("-published_at", "-created_at")
    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page") or 1
    try:
        notices = paginator.get_page(page_number)
    except EmptyPage:
        notices = paginator.get_page(paginator.num_pages)
    return render(request, "notices/notice_list.html", {"notices": notices})

def notice_detail(request, pk: int):
    notice = get_object_or_404(Notice.objects.filter(is_active=True), pk=pk)

    more_notices = (
        Notice.objects.filter(is_active=True)
        .exclude(pk=notice.pk)
        .order_by("-published_at", "-created_at")[:8]
    )
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

    return render(request, "notice_detail.html", {
        "notice": notice,
        "more_notices": more_notices,
        "prev_notice": prev_notice,
        "next_notice": next_notice,
    })

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

# -------------------------------------------------------------------
# Results pages
# -------------------------------------------------------------------

def results_index(request):
    """
    List/overview: shows paginated ClassResultSummary rows (class-level aggregates).
    """
    base_qs = (
        ClassResultSummary.objects
        .select_related("klass", "term")
        .order_by("-term__year", "term__name", "klass__name", "klass__section", "-id")
    )
    qs = _apply_result_filters(base_qs, request)

    paginator = Paginator(qs, 24)  # 24 summaries per page
    page = paginator.get_page(request.GET.get("page") or 1)

    # (Optional) filter dropdown data
    years = list(ExamTerm.objects.order_by("-year").values_list("year", flat=True).distinct())
    terms = ExamTerm.objects.order_by("name", "-year").values("id", "name", "year")
    classes = AcademicClass.objects.order_by("-year", "name", "section").values("id", "name", "section", "year")

    ctx = {
        "page": page,
        "summaries": page.object_list,
        "filters": {
            "year": request.GET.get("year") or "",
            "term_id": request.GET.get("term_id") or "",
            "class_id": request.GET.get("class_id") or "",
            "name": request.GET.get("name") or "",
            "section": request.GET.get("section") or "",
        },
        "years": years,
        "terms": terms,
        "classes": classes,
    }
    return render(request, "results/results_index.html", ctx)

def results_filter(request):
    """Alias to results_index (keeps {% url 'results:filter' %} working)."""
    return results_index(request)

def results_detail(request, summary_id: int):
    """
    Detail page for a given ClassResultSummary (one Class + one Term).
    Includes toppers and optional per-subject class averages.
    """
    summary = get_object_or_404(
        ClassResultSummary.objects.select_related("klass", "term").prefetch_related(
            Prefetch("toppers", queryset=summary_toppers_qs()),
            Prefetch(
                "subject_avgs",
                queryset=ClassResultSubjectAvg.objects.select_related("subject").order_by("subject__code"),
            ),
        ),
        pk=summary_id,
    )

    ctx = {
        "summary": summary,
        "klass": summary.klass,
        "term": summary.term,
        "toppers": summary.toppers.all(),           # already ordered by prefetch
        "subject_avgs": summary.subject_avgs.all(), # already ordered by prefetch
    }
    return render(request, "results/results_detail.html", ctx)

def results_debug(_):
    c = ClassResultSummary.objects.count()
    s = ClassResultSummary.objects.select_related("klass", "term").first()
    return HttpResponse(f"Summaries={c} | First={s}")

# -------------------------------------------------------------------
# Attendance JSON endpoints (backend for Class Attendance overview)
# -------------------------------------------------------------------

def _staff(user):
    return user.is_authenticated and user.is_staff

@login_required
@require_http_methods(["GET"])
def attendance_class_overview_json(request, class_id: int):
    """
    Overview for a class between start/end (inclusive), aggregated from per-day counts.
    Optional GET: start=YYYY-MM-DD, end=YYYY-MM-DD (defaults to last 30 days)
    """
    try:
        klass = AcademicClass.objects.get(pk=class_id)
    except AcademicClass.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    end = parse_date(request.GET.get("end") or "") or date.today()
    start = parse_date(request.GET.get("start") or "") or (end - timedelta(days=30))

    days = (AttendanceSession.objects
            .filter(school_class=klass, date__gte=start, date__lte=end)
            .order_by("date")
            .values("date", "present_count", "absent_count", "late_count", "excused_count"))

    by_day = []
    totals = {"present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0}

    for d in days:
        present = int(d["present_count"] or 0)
        absent  = int(d["absent_count"]  or 0)
        late    = int(d["late_count"]    or 0)
        excused = int(d["excused_count"] or 0)
        total   = present + absent + late + excused
        rate    = round(100.0 * (present + excused) / total, 1) if total else 0.0

        by_day.append({
            "date": d["date"].isoformat(),
            "present": present, "absent": absent, "late": late, "excused": excused,
            "total": total, "rate_pct": rate,
        })

        totals["present"] += present
        totals["absent"]  += absent
        totals["late"]    += late
        totals["excused"] += excused
        totals["total"]   += total

    return JsonResponse({
        "klass": {"id": klass.id, "name": klass.name},
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "totals": totals,
        "by_day": by_day,
    })


@login_required
@user_passes_test(_staff)
@require_http_methods(["GET"])
def attendance_classday_get(request, class_id: int):
    """
    Get counts for a single class+date.
    GET: date=YYYY-MM-DD (defaults today)
    """
    try:
        klass = AcademicClass.objects.get(pk=class_id)
    except AcademicClass.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    the_date = parse_date(request.GET.get("date") or "") or date.today()

    day = AttendanceSession.objects.filter(school_class=klass, date=the_date).first()
    if not day:
        return JsonResponse({
            "class_id": klass.id,
            "date": the_date.isoformat(),
            "present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0, "rate_pct": 0.0,
        })

    present = int(day.present_count or 0)
    absent  = int(day.absent_count  or 0)
    late    = int(day.late_count    or 0)
    excused = int(day.excused_count or 0)
    total   = present + absent + late + excused
    rate    = round(100.0 * (present + excused) / total, 1) if total else 0.0

    return JsonResponse({
        "class_id": klass.id,
        "date": the_date.isoformat(),
        "present": present, "absent": absent, "late": late, "excused": excused,
        "total": total, "rate_pct": rate,
    })


@login_required
@user_passes_test(_staff)
@require_http_methods(["POST"])
def attendance_classday_upsert(request):
    """
    Create/update a class-day with counts (no per-student rows).
    POST form-data:
      class_id (or klass_id)  required
      date                    YYYY-MM-DD (optional; defaults today)
      present, absent, late, excused   integers ≥ 0 (optional; default 0)
    """
    def _to_int(name):
        v = request.POST.get(name)
        if v in (None, ""):
            return 0
        try:
            return max(0, int(v))
        except ValueError:
            raise ValueError(f"{name} must be an integer ≥ 0")

    class_id = request.POST.get("class_id") or request.POST.get("klass_id")
    if not class_id:
        return HttpResponseBadRequest("class_id (or klass_id) required")

    try:
        klass = AcademicClass.objects.get(pk=class_id)
    except AcademicClass.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    the_date = parse_date(request.POST.get("date") or "") or date.today()

    try:
        present = _to_int("present")
        absent  = _to_int("absent")
        late    = _to_int("late")
        excused = _to_int("excused")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    day, _created = AttendanceSession.objects.get_or_create(
        school_class=klass, date=the_date, defaults={"created_by": request.user}
    )
    day.present_count = present
    day.absent_count  = absent
    day.late_count    = late
    day.excused_count = excused
    day.save(update_fields=["present_count", "absent_count", "late_count", "excused_count"])

    total = present + absent + late + excused
    rate  = round(100.0 * (present + excused) / total, 1) if total else 0.0

    return JsonResponse({
        "class_id": klass.id,
        "date": the_date.isoformat(),
        "present": present, "absent": absent, "late": late, "excused": excused,
        "total": total, "rate_pct": rate,
    }, status=200)
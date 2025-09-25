from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch, Count, Case, When, IntegerField
from django.apps import apps
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from content.models import (
    Banner, Notice, TimelineEvent, GalleryItem, AboutSection,
    AcademicCalendarItem, Course, FunctionHighlight, CollegeFestival, ContactInfo, FooterSettings, GalleryPost,
    ClassResultSummary, ClassTopper, ExamTerm, AcademicClass, ClassResultSubjectAvg, AttendanceRecord, AttendanceStatus,
    AttendanceSession
)
from content.forms import ContactForm

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


# ---------- views ----------
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
    years = list(
        ExamTerm.objects.order_by("-year").values_list("year", flat=True).distinct()
    )
    terms = ExamTerm.objects.order_by("name", "-year").values("id", "name", "year")
    classes = AcademicClass.objects.order_by("-year", "name", "section").values(
        "id", "name", "section", "year"
    )

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
    """
    A simple alias to results_index so `{% url 'results:filter' %}` works.
    If you make a dedicated filter UI template later, you can render it here.
    """
    return results_index(request)


def results_detail(request, summary_id: int):
    """
    Detail page for a given ClassResultSummary (one Class + one Term).
    Includes toppers and optional per-subject class averages.
    """
    summary = get_object_or_404(
        ClassResultSummary.objects.select_related("klass", "term")
        .prefetch_related(
            # toppers in rank order
            Prefetch("toppers", queryset=summary_toppers_qs()),
            # subject averages with subject loaded
            Prefetch(
                "subject_avgs",
                queryset=ClassResultSubjectAvg.objects.select_related("subject")
                .order_by("subject__code"),
            ),
        ),
        pk=summary_id,
    )

    ctx = {
        "summary": summary,
        "klass": summary.klass,
        "term": summary.term,
        "toppers": summary.toppers.all(),          # already ordered by prefetch
        "subject_avgs": summary.subject_avgs.all(),# already ordered by prefetch
    }
    return render(request, "results/results_detail.html", ctx)


# ---------- tiny query helper so we keep 'rank' order everywhere ----------
def summary_toppers_qs():
    from content.models import ClassTopper
    return ClassTopper.objects.order_by("rank", "id")


def class_results_overview(request):
    qs = (
        ClassResultSummary.objects
        .select_related("klass", "term")
        .order_by("-created_at", "klass__name", "klass__section")
    )
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "results/results_index.html",
        {
            "summaries": page_obj.object_list,
            "page_obj": page_obj,
        },
    )

def class_results_detail(request, summary_id: int):
    summary = get_object_or_404(
        ClassResultSummary.objects
        .select_related("klass", "term")
        .prefetch_related("toppers", "subject_avgs__subject"),
        pk=summary_id,
    )

    # Coerce to safe values so the template never shows blanks
    safe = {
        "total_students": summary.total_students or 0,
        "appeared": summary.appeared or 0,
        "pass_rate_pct": summary.pass_rate_pct or Decimal("0"),
        "overall_avg_pct": summary.overall_avg_pct or Decimal("0"),
        "highest_pct": summary.highest_pct or Decimal("0"),
        "lowest_pct": summary.lowest_pct or Decimal("0"),
    }

    return render(
        request,
        "results/class_overview.html",
        {
            "summary": summary,
            "klass": summary.klass,            # used in the heading
            "term": summary.term,              # used in the heading
            "safe": safe,                      # safe numbers for the cards
            "toppers": summary.toppers.all().order_by("rank", "id"),
            "subject_avgs": summary.subject_avgs.all().order_by("subject__code"),
        },
    )

def class_results_filter(request):
    # keep simple for now – you can extend later
    return render(request, "results/filter.html", {})


def results_index(request):
    qs = (ClassResultSummary.objects
          .select_related("klass", "term")
          .order_by("-created_at", "klass__name", "klass__section"))
    page = Paginator(qs, 20).get_page(request.GET.get("page") or 1)
    return render(request, "results/results_index.html", {
        "page": page,
        "summaries": page.object_list,
    })

def results_detail(request, summary_id: int):
    s = get_object_or_404(
        ClassResultSummary.objects
        .select_related("klass", "term")
        .prefetch_related("toppers", "subject_avgs__subject"),
        pk=summary_id
    )
    # always provide numbers (no blanks)
    safe = {
        "total":     s.total_students or 0,
        "appeared":  s.appeared or 0,
        "pass_pct":  s.pass_rate_pct or Decimal("0"),
        "avg_pct":   s.overall_avg_pct or Decimal("0"),
        "hi":        s.highest_pct or Decimal("0"),
        "lo":        s.lowest_pct or Decimal("0"),
    }
    return render(request, "results/class_overview.html", {
        "summary": s,
        "klass": s.klass,
        "term": s.term,
        "safe": safe,
        "toppers": s.toppers.all().order_by("rank", "id"),
        "subject_avgs": s.subject_avgs.all().order_by("subject__code"),
    })

# (optional) quick sanity page
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest


def results_debug(_):
    c = ClassResultSummary.objects.count()
    s = ClassResultSummary.objects.select_related("klass","term").first()
    return HttpResponse(f"Summaries={c} | First={s}")









CLASS_MODEL_LABEL   = getattr(settings, "ATTENDANCE_CLASS_MODEL",   "academics.Classroom")
STUDENT_MODEL_LABEL = getattr(settings, "ATTENDANCE_STUDENT_MODEL", "students.Student")
ROSTER_ATTR         = getattr(settings, "ATTENDANCE_ROSTER_ATTR",   "students")

def _model(label: str):
    app_label, model_name = label.split(".", 1)
    return apps.get_model(app_label, model_name)

ClassModel = _model(CLASS_MODEL_LABEL)

def _staff(user): return user.is_authenticated and user.is_staff


@login_required
@require_http_methods(["GET"])
def attendance_class_overview_json(request, class_id: int):
    """
    GET ?start=YYYY-MM-DD&end=YYYY-MM-DD  (defaults last 30 days)
    Aggregated totals + per-day breakdown for one class.
    """
    try:
        school_class = ClassModel.objects.get(pk=class_id)
    except ClassModel.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    end   = parse_date(request.GET.get("end") or "")   or date.today()
    start = parse_date(request.GET.get("start") or "") or (end - timedelta(days=30))

    qs = AttendanceRecord.objects.filter(
        session__school_class=school_class,
        session__date__gte=start,
        session__date__lte=end,
    )

    agg = qs.aggregate(
        present=Count(Case(When(status=AttendanceStatus.PRESENT, then=1), output_field=IntegerField())),
        absent =Count(Case(When(status=AttendanceStatus.ABSENT,  then=1), output_field=IntegerField())),
        late   =Count(Case(When(status=AttendanceStatus.LATE,    then=1), output_field=IntegerField())),
        excused=Count(Case(When(status=AttendanceStatus.EXCUSED, then=1), output_field=IntegerField())),
        total  =Count("id"),
    )

    per_day = (
        qs.values("session__date")
          .annotate(
              present=Count(Case(When(status=AttendanceStatus.PRESENT, then=1), output_field=IntegerField())),
              absent =Count(Case(When(status=AttendanceStatus.ABSENT,  then=1), output_field=IntegerField())),
              late   =Count(Case(When(status=AttendanceStatus.LATE,    then=1), output_field=IntegerField())),
              excused=Count(Case(When(status=AttendanceStatus.EXCUSED, then=1), output_field=IntegerField())),
              total  =Count("id"),
          )
          .order_by("session__date")
    )

    by_day = []
    for row in per_day:
        total = row["total"] or 1
        rate  = round(100.0 * (row["present"] + row["excused"]) / total, 1)  # excused counts as not-absent
        by_day.append({
            "date": row["session__date"].isoformat(),
            "present": row["present"],
            "absent": row["absent"],
            "late": row["late"],
            "excused": row["excused"],
            "total": total,
            "rate_pct": rate,
        })

    return JsonResponse({
        "class": {"id": school_class.id, "name": getattr(school_class, "name", str(school_class))},
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "totals": agg,
        "by_day": by_day,
    })


@login_required
@user_passes_test(_staff)
@require_http_methods(["POST"])
def attendance_create_session(request):
    """
    Create a session for {class_id, date}; optionally populate student records from the class roster.
    POST form: class_id (required), date=YYYY-MM-DD (optional), populate=yes|no (default yes)
    """
    class_id = request.POST.get("class_id")
    if not class_id:
        return HttpResponseBadRequest("class_id required")

    try:
        school_class = ClassModel.objects.get(pk=class_id)
    except ClassModel.DoesNotExist:
        return JsonResponse({"error": "Class not found"}, status=404)

    the_date = parse_date(request.POST.get("date") or "") or date.today()
    populate = (request.POST.get("populate") or "yes").lower() in ("1", "true", "yes")

    session, created = AttendanceSession.objects.get_or_create(
        school_class=school_class,
        date=the_date,
        defaults={"created_by": request.user},
    )

    created_records = 0
    if populate and created:
        roster = getattr(school_class, ROSTER_ATTR, None) or getattr(school_class, "student_set", None)
        if roster and hasattr(roster, "all"):
            students = list(roster.all())
            bulk = [
                AttendanceRecord(
                    session=session, student=s,
                    status=AttendanceStatus.PRESENT, marked_by=request.user
                ) for s in students
            ]
            if bulk:
                AttendanceRecord.objects.bulk_create(bulk, ignore_conflicts=True)
                created_records = len(bulk)

    return JsonResponse({
        "session_id": session.id,
        "created": created,
        "created_records": created_records,
        "class": school_class.id,
        "date": the_date.isoformat(),
    }, status=201 if created else 200)


@login_required
@user_passes_test(_staff)
@require_http_methods(["POST"])
def attendance_update_record(request):
    """
    Update a student's record.
    POST: record_id OR (session_id & student_id), and any of: status(P/A/L/E), minutes_late, reason
    """
    record_id  = request.POST.get("record_id")
    session_id = request.POST.get("session_id")
    student_id = request.POST.get("student_id")

    if record_id:
        try:
            rec = AttendanceRecord.objects.get(pk=record_id)
        except AttendanceRecord.DoesNotExist:
            return JsonResponse({"error": "Record not found"}, status=404)
    else:
        if not (session_id and student_id):
            return HttpResponseBadRequest("Provide record_id OR session_id and student_id")
        try:
            rec = AttendanceRecord.objects.get(session_id=session_id, student_id=student_id)
        except AttendanceRecord.DoesNotExist:
            return JsonResponse({"error": "Record not found"}, status=404)

    status_val = request.POST.get("status")
    if status_val:
        if status_val not in {"P", "A", "L", "E"}:
            return HttpResponseBadRequest("Invalid status (use P/A/L/E)")
        rec.status = status_val

    if "minutes_late" in request.POST:
        try:
            rec.minutes_late = max(0, int(request.POST.get("minutes_late") or 0))
        except ValueError:
            return HttpResponseBadRequest("minutes_late must be integer ≥ 0")

    if "reason" in request.POST:
        rec.reason = request.POST.get("reason") or ""

    rec.marked_by = request.user
    rec.save(update_fields=["status", "minutes_late", "reason", "marked_by", "marked_at"])

    return JsonResponse({
        "record_id": rec.id,
        "status": rec.status,
        "minutes_late": rec.minutes_late,
        "reason": rec.reason,
        "marked_at": rec.marked_at.isoformat(),
    })

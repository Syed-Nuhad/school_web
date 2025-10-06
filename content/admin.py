# content/admin.py
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.sites import NotRegistered
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.conf import settings

from .models import (
    # Core content
    Banner,
    Notice,
    TimelineEvent,
    GalleryItem,
    AboutSection,
    AcademicCalendarItem,
    # Domain models
    Course,
    AdmissionApplication,
    FunctionHighlight,
    FestivalMedia,
    CollegeFestival,
    Member,
    ContactInfo,
    ContactMessage,
    FooterSettings,
    GalleryPost,
    AcademicClass,
    Subject,
    ExamTerm,
    ClassResultSubjectAvg,
    ClassResultSummary,
    ClassTopper,
    # Attendance + Exams
    AttendanceSession,
    ExamRoutine, BusRoute, BusStop, StudentMarksheetItem, StudentMarksheet, SiteBranding, Expense, Income,
    TuitionInvoice, TuitionPayment, ExpenseCategory, IncomeCategory, StudentProfile,
)
from .views import finance_overview, build_finance_context








# -------------------------------------------------------------------
# Access helpers
# -------------------------------------------------------------------
def is_student_user(user): return user.groups.filter(name__iexact="Student").exists()

def can_access_admin(user):
    return user.is_authenticated and user.is_staff and not is_student_user(user)

def can_delete_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact="Admin").exists()

# -------------------------------------------------------------------
# Small utilities
# -------------------------------------------------------------------
def _img_url(obj):
    url = ""
    if hasattr(obj, "image") and getattr(obj, "image"):
        try: url = obj.image.url
        except Exception: url = ""
    if not url and hasattr(obj, "image_url"):
        url = obj.image_url or ""
    return url

def _img_preview(file_field, height=70):
    try:
        if file_field and file_field.url:
            return format_html('<img src="{}" style="height:{}px;border-radius:6px;">',
                               file_field.url, height)
    except Exception:
        pass
    return "—"

def _thumb(obj, size=60):
    try:
        url = ""
        if getattr(obj, "thumbnail", None) and obj.thumbnail:
            url = obj.thumbnail.url
        elif getattr(obj, "image", None) and obj.image:
            url = obj.image.url
        if url:
            return format_html('<img src="{}" style="height:{}px;border-radius:6px">', url, size)
    except Exception:
        pass
    return "—"

# -------------------------------------------------------------------
# Base mixin
# -------------------------------------------------------------------
class OwnableAdminMixin(admin.ModelAdmin):
    def has_module_permission(self, request): return can_access_admin(request.user)
    def has_view_permission(self, request, obj=None): return can_access_admin(request.user)
    def has_add_permission(self, request): return can_access_admin(request.user)
    def has_change_permission(self, request, obj=None): return can_access_admin(request.user)
    def has_delete_permission(self, request, obj=None): return can_delete_admin(request.user)

    def save_model(self, request, obj, form, change):
        if hasattr(obj, "created_by") and not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        if hasattr(obj, "posted_by") and not getattr(obj, "posted_by_id", None):
            obj.posted_by = request.user
        if hasattr(obj, "published_at") and not getattr(obj, "published_at", None):
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)



@admin.register(SiteBranding)
class SiteBrandingAdmin(OwnableAdminMixin):
    list_display = ("site_name", "is_active", "logo_preview", "updated_at")
    list_filter  = ("is_active",)
    search_fields = ("site_name",)
    readonly_fields = ("logo_preview", "favicon_preview", "updated_at", "created_at")
    fieldsets = (
        (None, {"fields": ("is_active", "site_name")}),
        ("Logo", {"fields": ("logo", "logo_url", "logo_alt", "logo_preview")}),
        ("Favicon (optional)", {"fields": ("favicon", "favicon_url", "favicon_preview")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def logo_preview(self, obj):
        if obj.logo_src:
            return format_html('<img src="{}" style="max-height:60px;">', obj.logo_src)
        return "—"
    logo_preview.short_description = "Logo preview"

    def favicon_preview(self, obj):
        if obj.favicon_src:
            return format_html('<img src="{}" style="height:24px;width:24px;">', obj.favicon_src)
        return "—"
    favicon_preview.short_description = "Favicon preview"



# -------------------------------------------------------------------
# Banner
# -------------------------------------------------------------------
@admin.register(Banner)
class BannerAdmin(OwnableAdminMixin):
    list_display = ("title", "order", "is_active", "created_by", "thumb", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "button_text", "button_link", "created_by__username")
    ordering = ("order", "-created_at")
    readonly_fields = ("created_by", "preview", "created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("title", "subtitle", "image", "image_url",
                       "button_text", "button_link", "order", "is_active"),
            "description": "Tip: If both Image and Image URL are set, the uploaded image is used."
        }),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
        ("Preview", {"fields": ("preview",)}),
    )

    def thumb(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="height:38px">', url) if url else "—"
    thumb.short_description = "Image"

    def preview(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="max-width:100%;max-height:200px">', url) if url else "—"
    preview.short_description = "Preview"

# -------------------------------------------------------------------
# Notice
# -------------------------------------------------------------------
@admin.register(Notice)
class NoticeAdmin(OwnableAdminMixin):
    list_display = ("title", "is_active", "published_at", "thumb")
    list_filter = ("is_active", "published_at")
    search_fields = ("title", "subtitle")
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")
    readonly_fields = ("preview", "created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("title", "subtitle", "image", "image_url",
                       "link_url", "published_at", "is_active"),
            "description": "‘Read more’ uses Link URL if provided; else the internal page."
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
        ("Preview", {"fields": ("preview",)}),
    )

    def thumb(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="height:38px">', url) if url else "—"
    thumb.short_description = "Image"

    def preview(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="max-width:100%;max-height:220px">', url) if url else "—"
    preview.short_description = "Preview"

# -------------------------------------------------------------------
# TimelineEvent
# -------------------------------------------------------------------
@admin.register(TimelineEvent)
class TimelineEventAdmin(OwnableAdminMixin):
    list_display = ("title", "date", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "description")
    list_filter = ("is_active", "date")
    date_hierarchy = "date"
    raw_id_fields = ("created_by",)
    readonly_fields = ("created_by", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("title", "description", "date", "order", "is_active"),
                "description": "Sorted by Date, then Order (lower first)."}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# GalleryItem
# -------------------------------------------------------------------
@admin.register(GalleryItem)
class GalleryItemAdmin(OwnableAdminMixin):
    list_display = ("title", "kind", "place", "taken_at", "order", "is_active", "thumb")
    list_filter = ("kind", "is_active")
    search_fields = ("title", "place")
    ordering = ("order", "-taken_at", "-id")
    date_hierarchy = "taken_at"

    fieldsets = (
        (None, {"fields": ("is_active", "order", "title", "place", "taken_at", "kind"),
                "description": "Use local date/time; format YYYY-MM-DD HH:MM (24-hour)."}),
        ("Media", {"fields": ("image", "youtube_embed_url", "thumbnail"),
                   "description": "Image → upload; YouTube → paste embed/watch URL; optional custom thumbnail."}),
    )

    def thumb(self, obj):
        src = getattr(obj, "thumb_src", "") or ""
        return format_html('<img src="{}" style="height:38px;border-radius:6px;">', src) if src else "—"
    thumb.short_description = "Thumb"

# -------------------------------------------------------------------
# AboutSection
# -------------------------------------------------------------------
@admin.register(AboutSection)
class AboutSectionAdmin(OwnableAdminMixin):
    list_display = ("title", "college_name", "order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "college_name", "body", "bullets")
    ordering = ("order", "-updated_at")
    readonly_fields = ("preview_1", "preview_2", "preview_3", "preview_4", "created_at", "updated_at")

    fieldsets = (
        ("Visibility & Order", {"fields": ("is_active", "order")}),
        ("Text Content", {"fields": ("title", "college_name", "body", "bullets")}),
        ("Fading Images (up to 4)", {
            "fields": (("image_1", "image_1_alt", "preview_1"),
                       ("image_2", "image_2_alt", "preview_2"),
                       ("image_3", "image_3_alt", "preview_3"),
                       ("image_4", "image_4_alt", "preview_4"))}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def preview_1(self, obj): return _img_preview(getattr(obj, "image_1", None))
    preview_1.short_description = "Preview #1"
    def preview_2(self, obj): return _img_preview(getattr(obj, "image_2", None))
    preview_2.short_description = "Preview #2"
    def preview_3(self, obj): return _img_preview(getattr(obj, "image_3", None))
    preview_3.short_description = "Preview #3"
    def preview_4(self, obj): return _img_preview(getattr(obj, "image_4", None))
    preview_4.short_description = "Preview #4"

# -------------------------------------------------------------------
# AcademicCalendarItem
# -------------------------------------------------------------------
@admin.register(AcademicCalendarItem)
class AcademicCalendarItemAdmin(OwnableAdminMixin):
    list_display  = ("title", "date_text", "tone", "icon_class", "order", "is_active", "updated_at")
    list_filter   = ("is_active", "tone")
    search_fields = ("title", "date_text", "description")
    ordering      = ("order", "-updated_at")
    readonly_fields = ("created_by", "created_at", "updated_at")

    fields = ("is_active", "order", "title", "date_text", "description",
              "icon_class", "tone", "created_by", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# Course
# -------------------------------------------------------------------
@admin.register(Course)
class CourseAdmin(OwnableAdminMixin):
    list_display = (
        "title", "category",
        "admission_fee_bdt", "first_month_tuition_bdt", "exam_fee_bdt",
        "bus_fee_bdt", "hostel_fee_bdt", "marksheet_fee_bdt",
        "order", "is_active", "updated_at", "thumb",
    )
    list_filter = ("is_active", "category")
    search_fields = ("title", "eligibility", "duration", "shift", "description")
    ordering = ("order", "-updated_at")
    readonly_fields = ("created_by", "created_at", "updated_at", "preview")

    fieldsets = (
        ("Visibility & Order", {"fields": ("is_active", "order")}),
        ("Basic Info", {"fields": ("title", "category", "duration", "shift", "eligibility")}),
        ("Media", {"fields": ("image", "syllabus_file", "preview")}),
        ("Details", {"fields": ("description",)}),
        ("Fees (BDT)", {"fields": ("admission_fee","first_month_tuition","exam_fee",
                                   "bus_fee","hostel_fee","marksheet_fee","monthly_fee")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def _bdt(self, v):
        try: return f"৳ {float(v):,.2f}"
        except Exception: return "—"

    def admission_fee_bdt(self, obj):       return self._bdt(obj.admission_fee)
    def first_month_tuition_bdt(self, obj): return self._bdt(obj.first_month_tuition)
    def exam_fee_bdt(self, obj):            return self._bdt(obj.exam_fee)
    def bus_fee_bdt(self, obj):             return self._bdt(obj.bus_fee)
    def hostel_fee_bdt(self, obj):          return self._bdt(obj.hostel_fee)
    def marksheet_fee_bdt(self, obj):       return self._bdt(obj.marksheet_fee)

    admission_fee_bdt.short_description       = "Admission"
    first_month_tuition_bdt.short_description = "Tuition (1st)"
    exam_fee_bdt.short_description            = "Exam"
    bus_fee_bdt.short_description             = "Bus"
    hostel_fee_bdt.short_description          = "Hostel"
    marksheet_fee_bdt.short_description       = "Marksheet"

    def thumb(self, obj):
        try:
            if obj.image and obj.image.url:
                return format_html('<img src="{}" style="height:38px;border-radius:6px;">', obj.image.url)
        except Exception:
            pass
        return "—"
    thumb.short_description = "Image"

    def preview(self, obj):
        try:
            if obj.image and obj.image.url:
                return format_html('<img src="{}" style="max-height:160px;max-width:100%;border-radius:8px;">', obj.image.url)
        except Exception:
            pass
        return "—"
    preview.short_description = "Preview"

# -------------------------------------------------------------------
# AdmissionApplication
# -------------------------------------------------------------------
@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(OwnableAdminMixin):
    list_display = (
        "full_name","desired_course",
        "add_admission","add_tuition","add_exam",
        "add_bus","add_hostel","add_marksheet",
        "fee_selected_total","payment_status","created_at",
    )
    list_filter  = ("payment_status","desired_course","add_bus","add_hostel","add_marksheet")
    search_fields= ("full_name","email","phone")
    readonly_fields = (
        "fee_admission","fee_tuition","fee_exam",
        "fee_bus","fee_hostel","fee_marksheet",
        "fee_base_subtotal","fee_selected_total","fee_total",
        "created_at",
    )

# -------------------------------------------------------------------
# FunctionHighlight
# -------------------------------------------------------------------
@admin.register(FunctionHighlight)
class FunctionHighlightAdmin(OwnableAdminMixin):
    list_display  = ("title", "place", "date_text", "order", "is_active")
    list_filter   = ("is_active",)
    search_fields = ("title", "place", "description")
    list_editable = ("order", "is_active")

# -------------------------------------------------------------------
# CollegeFestival (+ inline media)
# -------------------------------------------------------------------
class FestivalMediaInline(admin.TabularInline):
    model = FestivalMedia
    extra = 1
    fields = ("is_active", "order", "kind", "image", "youtube_url", "thumbnail", "caption", "preview")
    readonly_fields = ("preview",)
    def preview(self, obj): return _thumb(obj)
    preview.short_description = "Preview"

@admin.register(CollegeFestival)
class CollegeFestivalAdmin(OwnableAdminMixin):
    list_display  = ("title", "place", "date_text", "order", "is_active", "updated_at")
    list_filter   = ("is_active",)
    search_fields = ("title", "place", "description")
    ordering      = ("order", "-updated_at")
    inlines       = [FestivalMediaInline]
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Details", {"fields": ("is_active","order","title","slug","place","date_text","time_text","description")}),
        ("Hero Media", {"fields": ("hero_image","hero_video","hero_youtube_url"),
                        "description": "Provide a hero image, a video file, or a YouTube URL."}),
    )

# -------------------------------------------------------------------
# Member
# -------------------------------------------------------------------
@admin.register(Member)
class MemberAdmin(OwnableAdminMixin):
    list_display  = ("name","role","post","section","is_active","order","thumb","updated_at")
    list_filter   = ("is_active","role","section")
    search_fields = ("name","post","bio")
    list_editable = ("order","is_active")
    readonly_fields = ("created_by","created_at","updated_at","preview")

    fieldsets = (
        (None, {"fields": ("is_active","order","role","name","post","section","bio")}),
        ("Image", {"fields": ("photo","photo_url","preview"),
                   "description": "Upload photo or provide a direct photo URL."}),
        ("Audit", {"fields": ("created_by","created_at","updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

    def thumb(self, obj):
        src = obj.image_src
        return format_html('<img src="{}" style="height:38px;border-radius:6px;">', src) if src else "—"
    thumb.short_description = "Photo"

    def preview(self, obj):
        src = obj.image_src
        return format_html('<img src="{}" style="max-height:160px;max-width:100%;border-radius:8px;">', src) if src else "—"
    preview.short_description = "Preview"

# -------------------------------------------------------------------
# ContactInfo
# -------------------------------------------------------------------
@admin.register(ContactInfo)
class ContactInfoAdmin(OwnableAdminMixin):
    save_on_top = True
    list_display  = ("is_active", "address_short", "phone", "email")
    list_filter   = ("is_active",)
    search_fields = ("address", "phone", "email", "hours")
    readonly_fields = ("preview_map",)

    fieldsets = (
        ("Visibility", {"fields": ("is_active",)}),
        ("Details", {"fields": ("address", "phone", "email", "hours")}),
        ("Map", {"fields": ("map_embed_src", "preview_map"),
                 "description": "Paste a Google Maps embed URL (starts with https://www.google.com/maps/embed?...)."}),
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            "show_save": True,
            "show_save_and_continue": True,
            "show_save_and_add_another": True,
            "show_delete": self.has_delete_permission(request),
        })
        return super().changeform_view(request, object_id, form_url, extra_context)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_change_permission(request, obj)

    def address_short(self, obj):
        s = (getattr(obj, "address", "") or "").strip()
        return (s[:40] + "…") if len(s) > 40 else (s or "—")
    address_short.short_description = "Address"

    def preview_map(self, obj):
        src = getattr(obj, "map_embed_src", "") or ""
        if not src: return "—"
        return format_html('<iframe src="{}" width="100%" height="200" style="border:0;" allowfullscreen loading="lazy"></iframe>', src)
    preview_map.short_description = "Map Preview"

# -------------------------------------------------------------------
# ContactMessage
# -------------------------------------------------------------------
@admin.register(ContactMessage)
class ContactMessageAdmin(OwnableAdminMixin):
    list_display  = ("id", "name", "email", "subject")
    list_filter   = ()
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message")

# -------------------------------------------------------------------
# FooterSettings
# -------------------------------------------------------------------
@admin.register(FooterSettings)
class FooterSettingsAdmin(OwnableAdminMixin):
    list_display  = ("title", "is_active", "updated_at", "preview_logo")
    list_filter   = ("is_active",)
    search_fields = ("title", "address", "phone", "email", "copyright_name", "developer_name")
    readonly_fields = ("created_at", "updated_at", "preview_logo")

    fieldsets = (
        ("Visibility & Title", {"fields": ("is_active", "title")}),
        ("Contact", {"fields": ("address", "phone", "email")}),
        ("Quick Links", {
            "fields": ("link_home_enabled",
                       ("link_admission_label", "link_admission_url"),
                       ("link_results_label", "link_results_url"),
                       ("link_events_label", "link_events_anchor"))}),
        ("Social Links", {"fields": ("facebook_url", "whatsapp_url", "twitter_url", "email_linkto")}),
        ("Branding", {"fields": ("logo", "logo_url", "preview_logo"),
                      "description": "Upload a logo or provide a direct URL. Uploaded image wins."}),
        ("Credits", {"fields": ("copyright_name", "developer_name", "developer_url")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def preview_logo(self, obj):
        if not obj: return "—"
        src = obj.logo_src
        if not src: return "—"
        return format_html('<img src="{}" style="height:40px;">', src)
    preview_logo.short_description = "Logo Preview"

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# GalleryPost
# -------------------------------------------------------------------
@admin.register(GalleryPost)
class GalleryPostAdmin(OwnableAdminMixin):
    list_display  = ("title", "kind", "is_active", "order", "created_at")
    list_filter   = ("kind", "is_active", "created_at")
    search_fields = ("title", "youtube_url")
    ordering      = ("order", "-created_at")
    fieldsets = (
        (None, {"fields": ("is_active", "order", "title", "kind")}),
        ("Media", {"fields": ("image", "video", "youtube_url"),
                   "description": "Upload image for Image; MP4 for Video; or paste a YouTube link."}),
        ("Meta", {"fields": ("created_by",)}),
    )
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# ===================================================================
# ATTENDANCE
# ===================================================================

class SubjectInline(admin.TabularInline):
    model = Subject
    fk_name = "school_class"      # <- be explicit about the FK
    extra = 12                    # <- number of empty rows
    max_num = 200                 # <- optional: allow many
    fields = ("name", "is_active", "order")
    ordering = ("order", "name")
    show_change_link = True

@admin.register(AcademicClass)
class AcademicClassAdmin(OwnableAdminMixin):
    list_display  = ("name", "section", "year")
    list_filter   = ("year",)
    search_fields = ("name", "section")
    ordering      = ("-year", "name", "section")
    inlines       = [SubjectInline]

# If AttendanceSession got registered earlier in dev, ensure a clean state
try:
    admin.site.unregister(AttendanceSession)
except NotRegistered:
    pass

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(OwnableAdminMixin):
    list_display  = (
        "date", "school_class",
        "present_count", "absent_count", "late_count", "excused_count",
        "attendance_rate_pct", "created_by", "created_at",
    )
    list_filter   = ("school_class", "date")
    search_fields = ("school_class__name",)
    date_hierarchy = "date"
    autocomplete_fields = ("school_class",)

    fields = (
        "school_class", "date",
        ("present_count", "absent_count"),
        ("late_count", "excused_count"),
    )

    @admin.display(description="Rate %")
    def attendance_rate_pct(self, obj):
        p = int(obj.present_count or 0)
        a = int(obj.absent_count or 0)
        l = int(obj.late_count or 0)
        e = int(obj.excused_count or 0)
        total = p + a + l + e
        return round(100.0 * (p + e) / total, 1) if total else 0.0

# ===================================================================
# EXAM ROUTINES
# ===================================================================

@admin.register(ExamRoutine)
class ExamRoutineAdmin(OwnableAdminMixin):
    list_display = ("title_or_default", "school_class", "term", "date_span", "is_active", "updated_at", "thumb")
    list_filter  = ("is_active", "term", "school_class")
    search_fields = ("title", "school_class__name", "school_class__section", "term__name", "term__year")
    readonly_fields = ("created_by", "created_at", "updated_at", "preview")

    fieldsets = (
        ("Visibility", {"fields": ("is_active",)}),
        ("Who / When", {"fields": ("school_class", "term", ("exam_start_date", "exam_end_date"))}),
        ("Title & Notes", {"fields": ("title", "notes")}),
        ("Media", {"fields": ("routine_image", "routine_image_url", "preview"),
                   "description": "Upload the routine image or paste a direct image URL. Uploaded image wins."}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    autocomplete_fields = ("school_class", "term")

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

    def title_or_default(self, obj):
        return obj.title or f"{obj.school_class} — {obj.term}"
    title_or_default.short_description = "Title"

    def date_span(self, obj):
        if obj.exam_end_date and obj.exam_end_date != obj.exam_start_date:
            return f"{obj.exam_start_date} → {obj.exam_end_date}"
        return f"{obj.exam_start_date}"
    date_span.short_description = "Exam dates"

    def thumb(self, obj):
        src = obj.image_src
        return format_html('<img src="{}" style="height:38px;border-radius:6px;">', src) if src else "—"
    thumb.short_description = "Image"

    def preview(self, obj):
        src = obj.image_src
        return format_html('<img src="{}" style="max-height:260px;max-width:100%;border-radius:8px;">', src) if src else "—"
    preview.short_description = "Preview"

@admin.register(ExamTerm)
class ExamTermAdmin(OwnableAdminMixin):
    list_display  = ("name", "year")
    list_filter   = ("year",)
    search_fields = ("name",)   # required for autocomplete
    ordering      = ("-year", "name")



class BusStopInline(admin.TabularInline):
    model = BusStop
    extra = 1
    fields = (
        "is_active", "order", "name", "landmark",
        "time_text_morning", "time_text_evening", "lat", "lng",
    )
    ordering = ("order", "id")

@admin.register(BusRoute)
class BusRouteAdmin(OwnableAdminMixin):
    list_display = (
        "name", "code", "is_active", "driver_name", "driver_phone",
        "vehicle_plate", "vehicle_capacity", "order", "updated_at"
    )
    list_filter = ("is_active",)
    search_fields = ("name", "code", "driver_name", "driver_phone", "assistant_name", "assistant_phone", "notes")
    ordering = ("order", "name")
    inlines = [BusStopInline]
    readonly_fields = ("created_by", "created_at", "updated_at", "preview")

    fieldsets = (
        ("Visibility & Order", {"fields": ("is_active", "order")}),
        ("Basics", {"fields": ("name", "code", ("start_point", "end_point"), "operating_days_text")}),
        ("Contacts & Vehicle", {"fields": (
            ("driver_name", "driver_phone"),
            ("assistant_name", "assistant_phone"),
            ("vehicle_plate", "vehicle_capacity"),
            "fare_info",
        )}),
        ("Map & Media", {"fields": ("route_image", "route_image_url", "map_embed_src", "preview")}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

    def preview(self, obj):
        try:
            src = obj.image_src
            if src:
                return format_html('<img src="{}" style="max-height:200px;max-width:100%;border-radius:8px;">', src)
        except Exception:
            pass
        return "—"
    preview.short_description = "Preview"



class StudentMarksheetItemInline(admin.TabularInline):
    model = StudentMarksheetItem
    extra = 0
    fields = ("subject", "max_marks", "marks_obtained", "grade_letter", "remark", "order")
    autocomplete_fields = ("subject",)
    ordering = ("order", "id")

class StudentMarksheetAdminForm(forms.ModelForm):
    class Meta:
        model = StudentMarksheet
        fields = "__all__"

# -------- Subject admin (no assumptions about field names) --------
@admin.register(Subject)
class SubjectAdmin(OwnableAdminMixin):
    list_display  = ("name", "school_class", "is_active", "order")
    list_filter   = ("school_class", "is_active")
    search_fields = ("name", "school_class__name", "school_class__section")
    autocomplete_fields = ("school_class",)
    ordering = ("school_class", "order", "name")
    @admin.display(description="Class")
    def _subject_class(self, obj):
        return getattr(obj, "academic_class", None) or getattr(obj, "school_class", None) or "—"


# --- list_filter helper for StudentMarksheetItem by subject's class ---
class SubjectClassFilter(admin.SimpleListFilter):
    title = "Class"
    parameter_name = "class_id"

    def lookups(self, request, model_admin):
        classes = AcademicClass.objects.order_by("-year", "name", "section") \
            .values_list("id", "name", "section", "year")
        return [
            (str(cid), f"{name}{('-' + section) if section else ''} ({year})")
            for cid, name, section, year in classes
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subject__school_class_id=self.value())
        return queryset


@admin.register(StudentMarksheet)
class StudentMarksheetAdmin(OwnableAdminMixin):
    form = StudentMarksheetAdminForm
    inlines = [StudentMarksheetItemInline]
    # ... your list_display / fieldsets unchanged ...

    def save_model(self, request, obj, form, change):
        creating = obj.pk is None
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

        # If it's a brand-new marksheet (or has no items yet), create one row per subject for the selected class.
        if obj.school_class_id and (creating or obj.items.count() == 0):
            subjects = (Subject.objects
                        .filter(school_class_id=obj.school_class_id, is_active=True)
                        .order_by("order", "name", "id"))
            items = []
            order = 1
            for s in subjects:
                items.append(StudentMarksheetItem(
                    marksheet=obj,
                    subject=s,
                    max_marks=100,
                    marks_obtained=0,
                    order=order,
                ))
                order += 1
            if items:
                StudentMarksheetItem.objects.bulk_create(items)

        # Recalc totals after any potential new items.
        obj.recalc_totals()
        obj.save(update_fields=["total_marks", "total_grade", "updated_at"])


@admin.register(StudentMarksheetItem)
class StudentMarksheetItemAdmin(OwnableAdminMixin):
    list_display  = ("marksheet", "subject", "marks_obtained", "max_marks", "grade_letter", "order")
    list_filter   = (SubjectClassFilter,)
    search_fields = (
        "marksheet__student_full_name",
        "marksheet__roll_number",
        "subject__name",
    )
    # ✅ only subject is autocompleted (SubjectAdmin already has search_fields)
    autocomplete_fields = ("subject",)
    # ✅ avoid the admin.E039/E040 checks for the parent FK
    raw_id_fields = ("marksheet",)




@admin.register(IncomeCategory)
class IncomeCategoryAdmin(OwnableAdminMixin):
    list_display = ("name", "code", "is_fixed", "is_active")
    list_filter  = ("is_fixed", "is_active")
    search_fields = ("name", "code")


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(OwnableAdminMixin):
    list_display = ("name", "code", "is_fixed", "is_active")
    list_filter  = ("is_fixed", "is_active")
    search_fields = ("name", "code")


@admin.register(Income)
class IncomeAdmin(OwnableAdminMixin):
    list_display = ("date", "category", "amount", "description")
    list_filter  = ("category", "date")
    search_fields = ("description", "category__name")
    date_hierarchy = "date"

    # Inline total in changelist
    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        total = qs.aggregate(total=Sum("amount"))["total"] or 0
        extra_context = extra_context or {}
        extra_context["inline_total"] = total
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Expense)
class ExpenseAdmin(OwnableAdminMixin):
    list_display = ("date", "category", "amount", "vendor", "description")
    list_filter  = ("category", "date")
    search_fields = ("description", "vendor")
    date_hierarchy = "date"


class TuitionPaymentInline(admin.TabularInline):
    model = TuitionPayment
    extra = 0
    fields = ("amount", "provider", "txn_id", "paid_on")
    readonly_fields = ()
    show_change_link = True


@admin.register(TuitionInvoice)
class TuitionInvoiceAdmin(OwnableAdminMixin):
    list_display = ("student", "period_year", "period_month", "tuition_amount", "paid_amount", "balance", "due_date")
    list_filter  = ("period_year", "period_month")
    search_fields = ("student__email", "student__username")
    inlines = [TuitionPaymentInline]

    actions = ["print_outstanding"]

    def print_outstanding(self, request, queryset):
        """
        Opens the printable Outstanding Tuition view with only selected invoices
        (when none selected, we print all outstanding for current month).
        """
        ids = list(queryset.values_list("id", flat=True))
        request.session["finance_outstanding_ids"] = ids
        self.message_user(request, "Opening printable outstanding list…")
        from django.urls import reverse
        return TemplateResponse(request, "admin/finance/overview.html", {
            "trigger_only_outstanding": True,  # the view will compute outstanding anyway
        })
    print_outstanding.short_description = "Open printable Outstanding Tuition list"


# ---- Admin-level Finance Overview page (URL under admin/finance/overview) ----
class FinanceAdminSiteMixin(OwnableAdminMixin):
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("overview/", self.admin_site.admin_view(self.finance_overview_view), name="finance-overview"),
        ]
        return custom + urls

    def finance_overview_view(self, request):
        """
        Uses the same template as our view; admin wrapper only.
        """
        context = {"title": "Finance Overview"}
        return TemplateResponse(request, "admin/finance/overview.html", context)

# Attach mixin to a harmless model so the URL mounts under admin.
# (Alternative is AdminSite-level get_urls; keeping it simple here.)
# Register only if not already registered; you can also attach this to IncomeAdmin if you prefer.
# =========================== END: Finance Admin ===========================


def finance_overview_admin(request):
    ctx = admin.site.each_context(request)            # admin chrome (nav/sidebar)
    ctx.update(build_finance_context(request))        # your finance data
    ctx.setdefault("title", "Finance Overview")
    return TemplateResponse(request, "admin/finance/overview.html", ctx)


@admin.register(StudentProfile)
class StudentProfileAdmin(OwnableAdminMixin):
    list_display = ("user", "school_class", "section", "roll_number", "joined_on")
    list_filter = ("school_class__year", "school_class__name", "section")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email", "roll_number")
    ordering = ("school_class", "section", "roll_number")





@staff_member_required
def student_ledger_admin(request):
    ctx = {"title": "Student Ledger"}
    q_class = request.GET.get("class_id")
    q_section = (request.GET.get("section") or "").strip()
    q_roll = (request.GET.get("roll") or "").strip()

    student = None
    invoices = []
    totals = {}

    if q_class and q_roll:
        # You said “roll + class + section” identifies a student.
        # If you have a StudentProfile model, query that here to get the User.
        # Fallback: if your User model stores roll & section, adapt this query.
        profile = None
        try:
            from .models import StudentProfile
            qs = StudentProfile.objects.filter(school_class_id=q_class, roll_number=q_roll)
            if q_section:
                qs = qs.filter(section__iexact=q_section)
            profile = qs.select_related("user", "school_class").first()
        except Exception:
            profile = None

        if profile:
            student = profile.user
            ctx["profile"] = profile

            # Tuition invoices for this student
            invoices = (TuitionInvoice.objects
                        .filter(student=student)
                        .order_by("-period_year", "-period_month"))

            paid_months = invoices.filter(paid_amount__gte=models.F("tuition_amount")).count()
            due_months  = invoices.filter(paid_amount__lt=models.F("tuition_amount")).count()

            totals["tuition_paid"] = invoices.aggregate(s=Sum("paid_amount"))["s"] or 0
            totals["tuition_due"]  = invoices.aggregate(s=Sum(models.F("tuition_amount") - models.F("paid_amount")))["s"] or 0

            # Other fees, only if we added Income.student
            exam_cat = IncomeCategory.objects.filter(code="exam").first()
            bus_cat  = IncomeCategory.objects.filter(code="bus").first()

            totals["exam_fee"] = (Income.objects.filter(student=student, category=exam_cat)
                                               .aggregate(s=Sum("amount"))["s"] or 0) if exam_cat else 0
            totals["bus_fee"]  = (Income.objects.filter(student=student, category=bus_cat)
                                               .aggregate(s=Sum("amount"))["s"] or 0)  if bus_cat else 0

            totals["overall_paid"] = (Income.objects.filter(student=student)
                                                    .aggregate(s=Sum("amount"))["s"] or 0)

            ctx.update({
                "student": student,
                "invoices": invoices,
                "paid_months": paid_months,
                "due_months": due_months,
                "totals": totals,
            })
        else:
            messages.warning(request, "No student found for the given Class/Section/Roll.")

    ctx["classes"] = AcademicClass.objects.order_by("-year", "name")
    ctx["q"] = {"class_id": q_class, "section": q_section, "roll": q_roll}
    return render(request, "admin/finance/student_ledger.html", ctx)

# hook the URL into the admin
class FinanceAdminSite(admin.AdminSite):  # if you already have one, just add to get_urls
    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path("finance/student-ledger/", self.admin_view(student_ledger_admin), name="finance_student_ledger"),
        ]
        return extra + urls

# if you're using the default site, you can monkey-patch:
admin.site.get_urls = FinanceAdminSite().get_urls
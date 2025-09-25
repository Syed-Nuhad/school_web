# content/admin.py
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
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
    # Attendance
    AttendanceSession, ExamRoutine,
)

# -------------------------------------------------------------------
# Access helpers (single source of truth)
# -------------------------------------------------------------------
def is_student_user(user):
    return user.groups.filter(name__iexact="Student").exists()

def can_access_admin(user):
    """Allow any authenticated staff user into admin *except* members of 'Student'."""
    return user.is_authenticated and user.is_staff and not is_student_user(user)

def can_delete_admin(user):
    """Keep destructive delete to superusers or 'Admin' group."""
    return user.is_superuser or user.groups.filter(name__iexact="Admin").exists()

# -------------------------------------------------------------------
# Small utilities
# -------------------------------------------------------------------
def _img_url(obj):
    """Return an image URL from either ImageField `image` or text field `image_url`."""
    url = ""
    if hasattr(obj, "image") and getattr(obj, "image"):
        try:
            url = obj.image.url
        except Exception:
            url = ""
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
    """Show thumbnail if available; else image; else —"""
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
# Base mixin: unifies permissions + auto-ownership
# -------------------------------------------------------------------
class OwnableAdminMixin(admin.ModelAdmin):
    """
    - Grants view/add/change to any staff user not in 'Student'.
    - Keeps delete restricted (superuser or 'Admin' group).
    - Auto-sets created_by/posted_by/published_at if those fields exist.
    """
    # unified permissions
    def has_module_permission(self, request):
        return can_access_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return can_access_admin(request.user)

    def has_add_permission(self, request):
        return can_access_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return can_access_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_delete_admin(request.user)

    # auto-ownership & published_at (if present)
    def save_model(self, request, obj, form, change):
        if hasattr(obj, "created_by") and not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        if hasattr(obj, "posted_by") and not getattr(obj, "posted_by_id", None):
            obj.posted_by = request.user
        if hasattr(obj, "published_at") and not getattr(obj, "published_at", None):
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# Banner admin
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
            "fields": ("title", "subtitle", "image", "image_url", "button_text", "button_link", "order", "is_active"),
            "description": "Tip: If both <b>Image</b> and <b>Image URL</b> are set, the uploaded image is used."
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
# Notice admin
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
            "fields": ("title", "subtitle", "image", "image_url", "link_url", "published_at", "is_active"),
            "description": "‘Read more’ uses <b>Link URL</b> if provided; otherwise the internal detail page."
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
# TimelineEvent admin
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
        (None, {
            "fields": ("title", "description", "date", "order", "is_active"),
            "description": "Sorted by <b>Date</b>, then <b>Order</b> (lower first)."
        }),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# GalleryItem admin
# -------------------------------------------------------------------
@admin.register(GalleryItem)
class GalleryItemAdmin(OwnableAdminMixin):
    list_display = ("title", "kind", "place", "taken_at", "order", "is_active", "thumb")
    list_filter = ("kind", "is_active")
    search_fields = ("title", "place")
    ordering = ("order", "-taken_at", "-id")
    date_hierarchy = "taken_at"

    fieldsets = (
        (None, {
            "fields": ("is_active", "order", "title", "place", "taken_at", "kind"),
            "description": "Use local date/time; format: <b>YYYY-MM-DD HH:MM</b> (24-hour).",
        }),
        ("Media", {
            "fields": ("image", "youtube_embed_url", "thumbnail"),
            "description": "For images, upload <b>Image</b>. For YouTube, paste an <b>embed</b> or <b>watch</b> URL. Optional <b>Thumbnail</b> overrides the auto preview.",
        }),
    )

    def thumb(self, obj):
        src = getattr(obj, "thumb_src", "") or ""
        return format_html('<img src="{}" style="height:38px;border-radius:6px;">', src) if src else "—"
    thumb.short_description = "Thumb"

# -------------------------------------------------------------------
# AboutSection admin
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
            "fields": (
                ("image_1", "image_1_alt", "preview_1"),
                ("image_2", "image_2_alt", "preview_2"),
                ("image_3", "image_3_alt", "preview_3"),
                ("image_4", "image_4_alt", "preview_4"),
            ),
            "description": "Upload 1–4 images for the fade stack. Add alt text for accessibility."
        }),
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
# AcademicCalendarItem admin
# -------------------------------------------------------------------
@admin.register(AcademicCalendarItem)
class AcademicCalendarItemAdmin(OwnableAdminMixin):
    list_display  = ("title", "date_text", "tone", "icon_class", "order", "is_active", "updated_at")
    list_filter   = ("is_active", "tone")
    search_fields = ("title", "date_text", "description")
    ordering      = ("order", "-updated_at")
    readonly_fields = ("created_by", "created_at", "updated_at")

    fields = (
        "is_active",
        "order",
        "title",
        "date_text",
        "description",
        "icon_class",
        "tone",
        "created_by",
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# Course admin
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
        ("Fees (BDT)", {"fields": ("admission_fee","first_month_tuition","exam_fee","bus_fee","hostel_fee","marksheet_fee","monthly_fee")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    # --- helpers for BDT formatting in list_display ---
    def _bdt(self, v):
        try:
            return f"৳ {float(v):,.2f}"
        except Exception:
            return "—"

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
# AdmissionApplication admin
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
# FunctionHighlight admin
# -------------------------------------------------------------------
@admin.register(FunctionHighlight)
class FunctionHighlightAdmin(OwnableAdminMixin):
    list_display  = ("title", "place", "date_text", "order", "is_active")
    list_filter   = ("is_active",)
    search_fields = ("title", "place", "description")
    list_editable = ("order", "is_active")

# -------------------------------------------------------------------
# CollegeFestival admin (with inline media)
# -------------------------------------------------------------------
class FestivalMediaInline(admin.TabularInline):
    model = FestivalMedia
    extra = 1
    fields = ("is_active", "order", "kind", "image", "youtube_url", "thumbnail", "caption", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        return _thumb(obj)
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
                        "description": "Provide either a hero image, a video file, or a YouTube URL."}),
    )

# -------------------------------------------------------------------
# Member admin
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
                   "description": "Upload <b>photo</b> or provide a publicly accessible <b>photo URL</b>."}),
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
# ContactInfo admin
# -------------------------------------------------------------------
@admin.register(ContactInfo)
class ContactInfoAdmin(OwnableAdminMixin):
    """
    Fields present: is_active, address, phone, email, hours, map_embed_src
    """
    save_on_top = True  # keep a submit row at the top; Django also renders the bottom row

    list_display  = ("is_active", "address_short", "phone", "email")
    list_filter   = ("is_active",)
    search_fields = ("address", "phone", "email", "hours")
    readonly_fields = ("preview_map",)

    fieldsets = (
        ("Visibility", {"fields": ("is_active",)}),
        ("Details", {"fields": ("address", "phone", "email", "hours")}),
        ("Map", {
            "fields": ("map_embed_src", "preview_map"),
            "description": "Paste a Google Maps embed URL (the long one that starts with https://www.google.com/maps/embed?...).",
        }),
    )

    # Force all the standard action buttons to show
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            "show_save": True,
            "show_save_and_continue": True,
            "show_save_and_add_another": True,
            "show_delete": self.has_delete_permission(request),
        })
        return super().changeform_view(request, object_id, form_url, extra_context)

    # Let any staff user delete ContactInfo (override mixin’s stricter rule)
    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff

    # Superuser can always edit; others follow mixin rules
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
        if not src:
            return "—"
        return format_html(
            '<iframe src="{}" width="100%" height="200" style="border:0;" allowfullscreen loading="lazy"></iframe>',
            src
        )
    preview_map.short_description = "Map Preview"

# -------------------------------------------------------------------
# ContactMessage admin
# -------------------------------------------------------------------
@admin.register(ContactMessage)
class ContactMessageAdmin(OwnableAdminMixin):
    """Minimal, avoids non-existent fields like `is_resolved`."""
    list_display  = ("id", "name", "email", "subject")
    list_filter   = ()
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message")

# -------------------------------------------------------------------
# FooterSettings admin
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
            "fields": (
                "link_home_enabled",
                ("link_admission_label", "link_admission_url"),
                ("link_results_label", "link_results_url"),
                ("link_events_label", "link_events_anchor"),
            ),
            "description": "Leave a URL blank to hide that quick link."
        }),
        ("Social Links", {
            "fields": ("facebook_url", "whatsapp_url", "twitter_url", "email_linkto"),
            "description": "If Email Link is blank, footer uses the Contact email."
        }),
        ("Branding", {
            "fields": ("logo", "logo_url", "preview_logo"),
            "description": "Upload a logo or provide a direct URL. Uploaded image takes precedence."
        }),
        ("Credits", {"fields": ("copyright_name", "developer_name", "developer_url")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def preview_logo(self, obj):
        if not obj:
            return "—"
        src = obj.logo_src
        if not src:
            return "—"
        return format_html('<img src="{}" style="height:40px;">', src)
    preview_logo.short_description = "Logo Preview"

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)

# -------------------------------------------------------------------
# GalleryPost admin
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
                   "description": "Upload an image for Image type; MP4 for Video; or paste a YouTube link."}),
        ("Meta", {"fields": ("created_by",)}),
    )
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# ===================================================================
# ATTENDANCE — single, corrected registration (no duplicates)
# ===================================================================

@admin.register(AcademicClass)
class AcademicClassAdmin(OwnableAdminMixin):
    list_display  = ("name", "section", "year")
    search_fields = ("name", "section", "year")
    ordering      = ("-year", "name", "section")

# Unregister any previous AttendanceSession admin to avoid duplicates
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
    search_fields = ("school_class__name", "notes")
    date_hierarchy = "date"
    autocomplete_fields = ("school_class",)

    fields = (
        "school_class", "date",
        ("present_count", "absent_count"),
        ("late_count", "excused_count"),
        "notes",
    )




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
        ("Media", {
            "fields": ("routine_image", "routine_image_url", "preview"),
            "description": "Upload the routine image or paste a direct image URL. Uploaded image takes precedence."
        }),
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
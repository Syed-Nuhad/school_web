# content/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from .models import Course, AdmissionApplication

from .models import (
    Banner,
    Notice,
    TimelineEvent,
    GalleryItem,
    AboutSection,
    AcademicCalendarItem,
)

# -------------------------------------------------------------------
# Access helpers (single source of truth)
# -------------------------------------------------------------------
def is_student_user(user):
    return user.groups.filter(name__iexact="Student").exists()

def can_access_admin(user):
    """
    Allow any authenticated staff user into admin *except* members of 'Student'.
    """
    return user.is_authenticated and user.is_staff and not is_student_user(user)

def can_delete_admin(user):
    """
    Keep destructive delete to superusers or 'Admin' group.
    """
    return user.is_superuser or user.groups.filter(name__iexact="Admin").exists()

# -------------------------------------------------------------------
# Small utilities
# -------------------------------------------------------------------
def _img_url(obj):
    """
    Return an image URL from either ImageField `image` or text field `image_url`.
    """
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
        ("Visibility & Order", {
            "fields": ("is_active", "order"),
            "description": "Control whether this About block is visible and where it appears."
        }),
        ("Text Content", {
            "fields": ("title", "college_name", "body", "bullets"),
            "description": "Provide heading, sub-heading, a short paragraph, and bullets (one per line)."
        }),
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

    # IMPORTANT: do NOT include computed properties (like icon_tone_class) in `fields`
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


#
# If you already have OwnableAdminMixin in this file, reuse it. Otherwise remove the mixin.

@admin.register(Course)
class CourseAdmin(OwnableAdminMixin):
    list_display  = ("title", "category", "monthly_fee_display", "order", "is_active", "updated_at", "thumb")
    list_filter   = ("is_active", "category")
    search_fields = ("title", "eligibility", "duration", "shift", "description")
    ordering      = ("order", "-updated_at")
    readonly_fields = ("created_by", "created_at", "updated_at", "preview")

    fieldsets = (
        ("Visibility & Order", {"fields": ("is_active", "order")}),
        ("Basic Info", {"fields": ("title", "category", "duration", "shift", "eligibility")}),
        ("Media", {"fields": ("image", "syllabus_file", "preview")}),
        ("Details", {"fields": ("description",)}),
        ("Fees", {"fields": ("monthly_fee",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    # thumbnails / preview
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

    def monthly_fee_display(self, obj):
        return f"৳ {float(obj.monthly_fee):,.0f}" if obj.monthly_fee is not None else "—"
    monthly_fee_display.short_description = "Monthly Fee"

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)





@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "desired_course", "shift", "status", "created_at")
    list_filter  = ("status", "shift", "desired_course")
    search_fields = ("full_name", "email", "phone", "guardian_name", "previous_school")
    readonly_fields = ("created_at", "updated_at", "created_by")
    ordering = ("-created_at",)


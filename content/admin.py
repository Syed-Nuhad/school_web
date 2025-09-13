from django.contrib import admin
from django.utils.html import format_html

from .models import Banner, Notice, TimelineEvent, GalleryItem


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def is_admin_user(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()


def is_teacher_user(user):
    return user.groups.filter(name="Teacher").exists()


def _img_url(obj):
    """Return a usable image URL from either ImageField `image` or text field `image_url`."""
    url = ""
    if hasattr(obj, "image") and getattr(obj, "image"):
        try:
            url = obj.image.url
        except Exception:
            url = ""
    if not url and hasattr(obj, "image_url"):
        url = obj.image_url or ""
    return url


class OwnableAdminMixin(admin.ModelAdmin):
    """
    Auto-set created_by / posted_by on first save if the model has those fields.
    Also populate published_at for Notice on first save if missing.
    """
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin_user(request.user):
            return qs
        if is_teacher_user(request.user):
            if "created_by" in {f.name for f in Banner._meta.get_fields()}:
                return qs.filter(created_by=request.user)
            return qs.none()
        return qs.none()

    def has_module_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        if is_admin_user(request.user):
            return True
        if is_teacher_user(request.user):
            if obj is None:
                return True
            if hasattr(obj, "created_by_id"):
                return obj.created_by_id == request.user.id
        return False

    def has_delete_permission(self, request, obj=None):
        return is_admin_user(request.user)

    # thumbnails
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
class NoticeAdmin(admin.ModelAdmin):
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

    def has_module_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return is_admin_user(request.user)


# -------------------------------------------------------------------
# TimelineEvent admin
# -------------------------------------------------------------------
@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
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
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin_user(request.user):
            return qs
        if is_teacher_user(request.user):
            return qs.filter(created_by=request.user)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        if is_admin_user(request.user):
            return True
        if is_teacher_user(request.user):
            return obj is None or obj.created_by_id == request.user.id
        return False

    def has_delete_permission(self, request, obj=None):
        return is_admin_user(request.user)


# -------------------------------------------------------------------
# GalleryItem admin
# -------------------------------------------------------------------
@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
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

    def has_module_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return is_admin_user(request.user)

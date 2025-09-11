# content/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Banner, Notice, TimelineEvent


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def is_admin_user(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()

def is_teacher_user(user):
    return user.groups.filter(name="Teacher").exists()

def _img_url(obj):
    """
    Return a usable image URL from either ImageField `image` or text field `image_url`.
    Safe if either/both are missing.
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

def _filter_existing_fields(model, names):
    """
    Return only the field names that actually exist on `model`.
    Prevents admin from breaking if optional fields (like `image_url`) are not present.
    """
    existing = set(f.name for f in model._meta.get_fields())
    return tuple(n for n in names if n in existing)


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
# Banner admin (Teachers + Admin; teacher edits own, admin edits all)
# -------------------------------------------------------------------


@admin.register(Banner)
class BannerAdmin(OwnableAdminMixin):
    list_display = ("title", "order", "is_active", "created_by", "thumb", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "button_text", "button_link", "created_by__username")
    ordering = ("order", "-created_at")
    readonly_fields = ("created_by", "preview", "created_at", "updated_at")

    def get_fields(self, request, obj=None):
        base = (
            "title", "subtitle",
            "image",        # optional ImageField
            "image_url",    # optional URL/text field
            "preview",
            "button_text", "button_link",
            "order", "is_active",
            "created_by", "created_at", "updated_at",
        )
        return _filter_existing_fields(Banner, base)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin_user(request.user):
            return qs
        if is_teacher_user(request.user):
            # teacher sees only their banners
            if "created_by" in {f.name for f in Banner._meta.get_fields()}:
                return qs.filter(created_by=request.user)
            return qs.none()
        return qs.none()

    # permissions: teachers + admin can access; only admin can delete
    def has_module_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_change_permission(self, request, obj=None):
        if is_admin_user(request.user):
            return True
        if is_teacher_user(request.user):
            # teacher may edit only their own banner
            if obj is None:
                return True  # needed to render change list
            if hasattr(obj, "created_by_id"):
                return obj.created_by_id == request.user.id
        return False

    def has_delete_permission(self, request, obj=None):
        return is_admin_user(request.user)

    def thumb(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="height:38px">', url) if url else "—"
    thumb.short_description = "Image"

    def preview(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="max-width:100%;max-height:200px">', url) if url else "—"
    preview.short_description = "Preview"


# -------------------------------------------------------------------
# Notice admin (Teachers + Admin; teacher edits own, admin edits all)
# -------------------------------------------------------------------



def is_admin_user(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()

def is_teacher_user(user):
    return user.groups.filter(name="Teacher").exists()

def _img_url(obj):
    if getattr(obj, "image", None):
        try:
            return obj.image.url
        except Exception:
            pass
    return getattr(obj, "image_url", "") or ""

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display  = ("title", "is_active", "published_at", "thumb")
    list_filter   = ("is_active", "published_at")
    search_fields = ("title", "subtitle")
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")
    readonly_fields = ("preview", "created_at", "updated_at")

    fields = (
        "title",
        "subtitle",
        "image", "image_url",
        "preview",
        "link_url",
        "published_at",
        "is_active",
        "created_at", "updated_at",
    )

    def thumb(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="height:38px">', url) if url else "—"
    thumb.short_description = "Image"

    def preview(self, obj):
        url = _img_url(obj)
        return format_html('<img src="{}" style="max-width:100%;max-height:220px">', url) if url else "—"
    preview.short_description = "Preview"

    # permissions: teachers + admins can view/add/edit; delete stays admin-only
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
# TimelineEvent admin (Teachers + Admin; teacher edits own, admin edits all)
# -------------------------------------------------------------------
@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "date", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "description")
    list_filter = ("is_active", "date")

    # Avoid admin.E039 when User admin isn't registered.
    raw_id_fields = ("created_by",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin_user(request.user):
            return qs
        if is_teacher_user(request.user):
            return qs.filter(created_by=request.user)
        return qs.none()

    def has_module_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return is_admin_user(request.user) or is_teacher_user(request.user)

    def has_change_permission(self, request, obj=None):
        if is_admin_user(request.user):
            return True
        if is_teacher_user(request.user):
            return obj is None or getattr(obj, "created_by_id", None) == request.user.id
        return False

    def has_delete_permission(self, request, obj=None):
        # Only Admins can delete timeline events
        return is_admin_user(request.user)

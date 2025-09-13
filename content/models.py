from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
import re


User = settings.AUTH_USER_MODEL


def banner_upload_to(instance, filename):
    return f"banners/{timezone.now():%Y/%m}/{filename}"


def notice_upload_to(instance, filename):
    return f"notices/{timezone.now():%Y/%m}/{filename}"


# //////////////////////////////////
# Banner
# //////////////////////////////////
class Banner(models.Model):
    """Homepage slider banner with optional image file or external URL."""
    title = models.CharField(
        max_length=150,
        help_text="Main headline shown on the banner."
    )
    subtitle = models.CharField(
        max_length=300, blank=True,
        help_text="Optional sub-headline under the title."
    )

    image = models.ImageField(
        upload_to=banner_upload_to, blank=True, null=True,
        help_text="Preferred ~1920×600 JPG/PNG. Ignored if Image URL is set."
    )
    image_url = models.URLField(
        blank=True,
        help_text="External image URL (used if no uploaded image or if set)."
    )

    button_text = models.CharField(
        max_length=40, blank=True,
        help_text="Optional CTA text (e.g. ‘Apply now’)."
    )
    button_link = models.CharField(
        max_length=300, blank=True,
        help_text="Internal path or full URL (e.g. /admission or https://example.com)."
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this banner."
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="banners_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "-created_at")

    def __str__(self):
        return self.title

    @property
    def image_src(self) -> str:
        """Prefer uploaded file; fall back to external URL; never crash."""
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return self.image_url or ""

    def clean(self):
        """Trim fields and require at least one image source."""
        for f in ("title", "subtitle", "button_text", "button_link", "image_url"):
            v = getattr(self, f, "")
            if isinstance(v, str):
                setattr(self, f, v.strip())

        if not self.image and not (self.image_url or "").strip():
            raise ValidationError("Provide an image file or an image URL.")


# //////////////////////////////////
# Notice
# //////////////////////////////////
class Notice(models.Model):
    title = models.CharField(
        max_length=200,
        help_text="Notice title shown on the card."
    )
    subtitle = models.TextField(
        blank=True,
        help_text="Optional short description shown under the title."
    )
    image = models.ImageField(
        upload_to=notice_upload_to, blank=True, null=True,
        help_text="Optional image for the notice card."
    )
    image_url = models.URLField(
        blank=True,
        help_text="Optional external image URL (used if no uploaded image)."
    )
    link_url = models.URLField(
        blank=True,
        help_text="Optional ‘Read more’ target; if empty, the internal detail page is used."
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        help_text="Publish date/time (controls ordering). Format: YYYY-MM-DD HH:MM (24-hour)."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this notice."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")

    def __str__(self):
        return self.title

    @property
    def image_src(self) -> str:
        if getattr(self, "image", None):
            try:
                return self.image.url
            except Exception:
                pass
        return getattr(self, "image_url", "") or ""

    def get_absolute_url(self) -> str:
        return reverse("notice_detail", args=[self.pk])

    @property
    def url(self) -> str:
        lu = getattr(self, "link_url", "") or ""
        return lu if lu.strip() else self.get_absolute_url()


# //////////////////////////////////
# Timeline
# //////////////////////////////////
class TimelineEvent(models.Model):
    title = models.CharField(
        max_length=150,
        help_text="Event title (shown on the timeline)."
    )
    description = models.TextField(
        blank=True,
        help_text="Optional short description under the title."
    )
    date = models.DateField(
        help_text="Event date (YYYY-MM-DD)."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Secondary sort within the same date. Lower appears first."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this event."
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="timeline_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("date", "order", "-created_at")

    def __str__(self):
        return f"{self.date} — {self.title}"


# //////////////////////////////////
# Gallery
# //////////////////////////////////
class GalleryItem(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    KIND_CHOICES = [(IMAGE, "Image"), (VIDEO, "YouTube (embed)")]

    kind = models.CharField(
        max_length=10, choices=KIND_CHOICES, default=IMAGE,
        help_text="Choose ‘Image’ to upload a photo or ‘YouTube (embed)’ for a video."
    )
    title = models.CharField(
        max_length=200,
        help_text="Display title for this item."
    )
    place = models.CharField(
        max_length=120, blank=True,
        help_text="Optional location (e.g., ‘Main Hall’)."
    )
    taken_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the photo/video was taken. Format: YYYY-MM-DD HH:MM (24-hour)."
    )

    # media
    image = models.ImageField(
        upload_to="gallery/", blank=True,
        help_text="Upload if Kind=Image. Recommended ~1600px on the long side."
    )
    youtube_embed_url = models.URLField(
        blank=True,
        help_text="For Kind=YouTube. You can paste either an embed URL or a watch URL "
                  "(e.g., https://www.youtube.com/embed/ScMzIvxBSi4 or "
                  "https://www.youtube.com/watch?v=ScMzIvxBSi4)."
    )
    thumbnail = models.ImageField(
        upload_to="gallery/thumbs/", blank=True,
        help_text="Optional custom thumbnail for grids (e.g., 600×400). If empty, a YouTube thumbnail or the main image is used."
    )

    # housekeeping
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this item."
    )

    class Meta:
        ordering = ["order", "-taken_at", "-id"]

    def __str__(self):
        return self.title

    # --- convenience ---
    @property
    def date_str(self):
        return self.taken_at.strftime("%Y-%m-%d") if self.taken_at else ""

    @property
    def time_str(self):
        # Portable (Windows-safe) 12-hour format without leading zero
        return self.taken_at.strftime("%I:%M %p").lstrip("0") if self.taken_at else ""

    def _youtube_id(self):
        if not self.youtube_embed_url:
            return ""
        m = re.search(r"(?:embed/|v=)([A-Za-z0-9_-]{11})", self.youtube_embed_url)
        return m.group(1) if m else ""

    @property
    def thumb_src(self) -> str:
        # priority: explicit thumbnail > youtube thumb > image
        if getattr(self, "thumbnail", None):
            try:
                return self.thumbnail.url
            except Exception:
                pass
        if self.kind == self.VIDEO:
            vid = self._youtube_id()
            if vid:
                return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
        if getattr(self, "image", None):
            try:
                return self.image.url
            except Exception:
                pass
        return ""

    def clean(self):
        """Basic sanity: require media for selected kind."""
        if self.kind == self.IMAGE and not self.image:
            raise ValidationError("For Kind=Image, please upload an image.")
        if self.kind == self.VIDEO and not (self.youtube_embed_url or "").strip():
            raise ValidationError("For Kind=YouTube, please provide a YouTube URL.")

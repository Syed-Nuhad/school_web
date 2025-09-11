from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


def banner_upload_to(instance, filename):
    return f"banners/{timezone.now():%Y/%m}/{filename}"

def notice_upload_to(instance, filename):
    return f"notices/{timezone.now():%Y/%m}/{filename}"


class Banner(models.Model):
    """Homepage slider banner with optional image file or external URL."""
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to=banner_upload_to, blank=True, null=True)
    image_url = models.URLField(blank=True)  # used if no file
    button_text = models.CharField(max_length=40, blank=True)
    button_link = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

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
        if self.image:
            try:
                return self.image.url
            except Exception:
                return ""
        return self.image_url or ""


User = settings.AUTH_USER_MODEL


class Notice(models.Model):
    title        = models.CharField(max_length=200)
    subtitle     = models.TextField(blank=True)                 # the paragraph under title
    image        = models.ImageField(upload_to="notices/", blank=True, null=True)
    image_url    = models.URLField(blank=True)                  # optional external image
    link_url     = models.URLField(blank=True)                  # "Read More" target
    published_at = models.DateTimeField(default=timezone.now)   # shown on the card
    is_active    = models.BooleanField(default=True)

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")

    def __str__(self):
        return self.title


    @property
    def image_src(self) -> str:
        """Already in your model: returns image.url or image_url or ''."""
        if getattr(self, "image", None):
            try:
                return self.image.url
            except Exception:
                pass
        return getattr(self, "image_url", "") or ""

    def get_absolute_url(self) -> str:
        """Canonical internal URL (detail page)."""
        return reverse("notice_detail", args=[self.pk])

    @property
    def url(self) -> str:
        """
        Preferred link target for 'Read more':
        - if link_url is set (external or custom), use that
        - otherwise, use the internal detail page
        """
        lu = getattr(self, "link_url", "") or ""
        return lu if lu.strip() else self.get_absolute_url()



class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def banner_upload_to(instance, filename):
    return f"banners/{timezone.now():%Y/%m}/{filename}"

def notice_upload_to(instance, filename):
    return f"notices/{timezone.now():%Y/%m}/{filename}"

class TimelineEvent(TimeStampedMixin):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="events_created"
    )
    title = models.CharField(max_length=200)
    date = models.DateField()  # the big date on the timeline (e.g., 2025-01-15)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("date", "order", "created_at")

    def __str__(self):
        return f"{self.date} — {self.title}"

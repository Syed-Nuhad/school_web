from django.conf import settings
from django.db import models
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


class Notice(models.Model):
    """
    Teacher-posted notice for the board.
    grade/section kept as free text for now; can be normalized later.
    """
    title = models.CharField(max_length=180)
    body = models.TextField()
    image = models.ImageField(upload_to=notice_upload_to, blank=True, null=True)
    image_url = models.URLField(blank=True)
    grade = models.CharField(max_length=50, blank=True)     # e.g. "Class 9"
    section = models.CharField(max_length=20, blank=True)   # e.g. "A", "Science"
    link_url = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="notices_posted"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")

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

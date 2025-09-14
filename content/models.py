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



def about_upload_to(instance, filename):
    return f"about/{timezone.now():%Y/%m}/{filename}"


class AboutSection(models.Model):
    """
    One editable 'About the College' block with up to 4 fading images.
    (Single model by request—no separate image table.)
    """
    # --- content ---
    title = models.CharField(
        max_length=150,
        help_text="Section heading shown above the block (e.g., 'About My College')."
    )
    college_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional sub-heading inside the block (e.g., your college name)."
    )
    body = models.TextField(
        blank=True,
        help_text="Main paragraph text. Keep it concise."
    )
    bullets = models.TextField(
        blank=True,
        help_text="Bullet points — one per line. Example:\nSmart Classrooms\nExperienced Faculty\nModern Labs"
    )

    # --- images (up to 4, optional) ---
    image_1 = models.ImageField(
        upload_to=about_upload_to, blank=True, null=True,
        help_text="Fading image #1 (landscape recommended)."
    )
    image_1_alt = models.CharField(
        max_length=200, blank=True,
        help_text="Alt text for image #1 (accessibility)."
    )

    image_2 = models.ImageField(
        upload_to=about_upload_to, blank=True, null=True,
        help_text="Fading image #2 (optional)."
    )
    image_2_alt = models.CharField(
        max_length=200, blank=True,
        help_text="Alt text for image #2 (accessibility)."
    )

    image_3 = models.ImageField(
        upload_to=about_upload_to, blank=True, null=True,
        help_text="Fading image #3 (optional)."
    )
    image_3_alt = models.CharField(
        max_length=200, blank=True,
        help_text="Alt text for image #3 (accessibility)."
    )

    image_4 = models.ImageField(
        upload_to=about_upload_to, blank=True, null=True,
        help_text="Fading image #4 (optional)."
    )
    image_4_alt = models.CharField(
        max_length=200, blank=True,
        help_text="Alt text for image #4 (accessibility)."
    )

    # --- ordering/visibility ---
    order = models.PositiveIntegerField(default=0, help_text="Lower comes first.")
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide this section.")

    # --- housekeeping ---
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("order", "-updated_at")
        verbose_name = "About Section"
        verbose_name_plural = "About Sections"

    def __str__(self):
        return self.title

    @property
    def bullet_list(self):
        """Return bullets as a cleaned list (skip blanks)."""
        return [b.strip() for b in (self.bullets or "").splitlines() if b.strip()]

    @property
    def image_list(self):
        """
        Returns a list of (url, alt) for all present images, in order.
        Useful in templates for the fading stack.
        """
        out = []
        for idx in (1, 2, 3, 4):
            img = getattr(self, f"image_{idx}", None)
            if img:
                try:
                    url = img.url
                except Exception:
                    url = ""
                if url:
                    alt = getattr(self, f"image_{idx}_alt", "") or ""
                    out.append((url, alt))
        return out

    @property
    def image_count(self):
        return len(self.image_list)

# ACADEMIC CALENDAR

class AcademicCalendarItem(models.Model):
    TONE_CHOICES = [
        ("blue", "Blue"),
        ("green", "Green"),
        ("red", "Red"),
        ("purple", "Purple"),
        ("orange", "Orange"),
    ]

    # Content
    title = models.CharField(
        max_length=150,
        help_text="Short heading (e.g., ‘Semester Start’)."
    )
    date_text = models.CharField(
        max_length=150,
        help_text="Human-friendly date or range (e.g., ‘10 Sep 2025’ or ‘20 Dec 2025 – 5 Jan 2026’)."
    )
    description = models.TextField(
        blank=True,
        help_text="Optional brief description shown under the date."
    )

    # Appearance
    icon_class = models.CharField(
        max_length=80,
        default="bi bi-calendar-event",
        help_text=(
            "CSS class for the icon.\n"
            "• Bootstrap Icons (load BI in base.html): e.g. bi bi-calendar-week\n"
            "• Font Awesome (if you load FA): e.g. fa-solid fa-calendar-days"
        ),
    )
    tone = models.CharField(
        max_length=10,
        choices=TONE_CHOICES,
        default="blue",
        help_text="Color accent for the round icon badge."
    )

    # Placement / lifecycle
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this item from the site."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="calendar_items",
        help_text="Auto-filled on first save."
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("order", "-updated_at")
        verbose_name = "Academic Calendar Item"
        verbose_name_plural = "Academic Calendar Items"

    def __str__(self):
        return self.title

    @property
    def icon_tone_class(self) -> str:
        return f"icon-{self.tone}"


    # Start Programs & Courses Section

def course_image_upload_to(instance, filename):
    return f"courses/{instance.category}/{filename}"

def course_syllabus_upload_to(instance, filename):
    return f"courses/syllabi/{instance.category}/{filename}"

class Course(models.Model):
    CATEGORY_CHOICES = [
        ("science", "Science"),
        ("commerce", "Commerce"),
        ("arts", "Arts"),
        ("vocational", "Vocational"),
    ]

    # Core
    title = models.CharField(
        max_length=150,
        help_text="Visible title of the course/program (e.g., “HSC – Science”)."
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES,
        help_text="Used by the front-end filter buttons."
    )

    # Media
    image = models.ImageField(
        upload_to=course_image_upload_to, blank=True, null=True,
        help_text="Card image shown at the top."
    )
    syllabus_file = models.FileField(
        upload_to=course_syllabus_upload_to, blank=True, null=True,
        help_text="Optional PDF to open with 'View Syllabus (PDF)'."
    )

    # Details
    duration = models.CharField(
        max_length=50, blank=True,
        help_text='Example: "2 years"'
    )
    shift = models.CharField(
        max_length=50, blank=True,
        help_text='Example: "Day", "Morning", "Evening"'
    )
    description = models.TextField(
        blank=True,
        help_text="Short paragraph shown on the card."
    )
    eligibility = models.CharField(
        max_length=200, blank=True,
        help_text='Example: "SSC pass (GPA ≥ 3.0)"'
    )
    monthly_fee = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Monthly fee in BDT. Leave blank if not applicable."
    )

    # Ordering / lifecycle
    order = models.PositiveIntegerField(default=0, help_text="Lower appears first.")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="courses_created",
        on_delete=models.SET_NULL, null=True, blank=True, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("order", "title")
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.title

# End Programs & Courses Section


# Admission app

def admission_photo_upload_to(instance, filename):
    return f"admissions/photos/{instance.created_at:%Y/%m}/{filename}"

def admission_doc_upload_to(instance, filename):
    return f"admissions/docs/{instance.created_at:%Y/%m}/{filename}"

class AdmissionApplication(models.Model):
    SHIFT_CHOICES = [
        ("day", "Day"),
        ("morning", "Morning"),
        ("evening", "Evening"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("review", "In review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    # Core
    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)

    # Course desired
    desired_course = models.ForeignKey(
        "content.Course",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="applications",
        help_text="Course the applicant is applying for."
    )
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, blank=True)

    # Academics
    previous_school = models.CharField(max_length=150, blank=True)
    ssc_gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Attachments
    photo = models.ImageField(upload_to=admission_photo_upload_to, null=True, blank=True)
    transcript = models.FileField(upload_to=admission_doc_upload_to, null=True, blank=True)

    # Extra
    message = models.TextField(blank=True)

    # Admin workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, editable=False,
        related_name="admissions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Admission Application"
        verbose_name_plural = "Admission Applications"

    def __str__(self):
        return f"{self.full_name} ({self.desired_course or '—'})"


# END
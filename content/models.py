# content/models.py
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, unquote

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F, Q
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



# //////////////////////////////////
# About
# //////////////////////////////////
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

# //////////////////////////////////
# ACADEMIC CALENDAR
# //////////////////////////////////
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


# //////////////////////////////////
# Programs & Courses
# //////////////////////////////////

def course_image_upload_to(instance, filename):
    """
    Upload path for a course's cover image.
    Kept simple so the path is stable even before the instance is saved.
    """
    return f"courses/{instance.category}/{filename}"


def course_syllabus_upload_to(instance, filename):
    """
    Upload path for a course's syllabus file (PDF/Doc, etc.).
    """
    return f"courses/syllabi/{instance.category}/{filename}"


class Course(models.Model):
    """
    A program that students can enroll into (e.g., Science, Commerce).
    Use the fee fields to publish a transparent, itemized cost breakdown
    in the frontend and to snapshot fees into applications.
    """

    CATEGORY_CHOICES = [
        ("science", "Science"),
        ("commerce", "Commerce"),
        ("arts", "Arts"),
        ("vocational", "Vocational"),
    ]

    title = models.CharField(
        max_length=150,
        help_text="Public name of the course as shown on the website.",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Bucket used for filtering and grouping courses.",
    )

    image = models.ImageField(
        upload_to=course_image_upload_to,
        blank=True, null=True,
        help_text="Optional cover image for cards/headers (recommended landscape).",
    )
    syllabus_file = models.FileField(
        upload_to=course_syllabus_upload_to,
        blank=True, null=True,
        help_text="Attach a PDF/DOC syllabus students can download.",
    )

    duration = models.CharField(
        max_length=50, blank=True,
        help_text="e.g., '2 years', 'Jan–Dec', or 'Semester based'.",
    )
    shift = models.CharField(
        max_length=50, blank=True,
        help_text="e.g., 'Morning', 'Day', 'Evening' (optional).",
    )
    description = models.TextField(
        blank=True,
        help_text="A short overview of what the course covers and outcomes.",
    )
    eligibility = models.CharField(
        max_length=200, blank=True,
        help_text="Minimum requirements (e.g., 'SSC pass with GPA ≥ 3.5').",
    )

    # >>> Fee fields you will set in admin <<<
    admission_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="One-time admission/registration fee.",
    )
    first_month_tuition = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Tuition fee for the first month (or initial installment).",
    )
    exam_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Internal/board exam fee (if applicable).",
    )
    bus_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Optional transport/bus fee (per month or fixed).",
    )
    hostel_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Optional hostel/accommodation fee.",
    )
    marksheet_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Optional marksheet/certification processing fee.",
    )

    # (optional legacy)
    monthly_fee = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Legacy field. Prefer the explicit fee fields above.",
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first in listings.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this course from the website.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="courses_created",
        on_delete=models.SET_NULL, null=True, blank=True, editable=False,
        help_text="User who created this record (set automatically).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, editable=False,
        help_text="When this record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True, editable=False,
        help_text="When this record was last updated.",
    )

    class Meta:
        ordering = ("order", "title")
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.title


# ---------- Admissions ----------

def admission_photo_upload_to(instance, filename):
    """
    Upload path for applicant photos. Uses current timestamp folders so it
    works before the object is saved to DB.
    """
    dt = timezone.now()
    return f"admissions/photos/{dt:%Y/%m}/{filename}"


def admission_doc_upload_to(instance, filename):
    """
    Upload path for applicant transcripts/attachments.
    """
    dt = timezone.now()
    return f"admissions/docs/{dt:%Y/%m}/{filename}"


class AdmissionApplication(models.Model):
    """
    A student's online admission form. We snapshot course fees into the application
    so that later fee changes in the Course model won't affect past applications.
    """

    full_name = models.CharField(
        max_length=200,
        help_text="Applicant’s full legal name.",
    )
    email = models.EmailField(
        blank=True,
        help_text="Applicant’s email (optional, but helps for communication).",
    )
    phone = models.CharField(
        max_length=20,
        help_text="Primary contact number (WhatsApp preferred if available).",
    )
    date_of_birth = models.DateField(
        blank=True, null=True,
        help_text="Optional, used for record verification.",
    )
    address = models.TextField(
        blank=True,
        help_text="Present address with district/upazila for correspondence.",
    )
    guardian_name = models.CharField(
        max_length=200, blank=True,
        help_text="Parent/guardian full name (optional).",
    )
    guardian_phone = models.CharField(
        max_length=20, blank=True,
        help_text="Parent/guardian phone number (optional).",
    )

    desired_course = models.ForeignKey(
        "content.Course",
        on_delete=models.PROTECT,
        related_name="applications",
        null=True, blank=True,
        help_text="The course the applicant is applying to.",
    )
    shift = models.CharField(
        max_length=20, blank=True,
        help_text="Preferred shift (Morning/Day/Evening).",
    )

    previous_school = models.CharField(
        max_length=200, blank=True,
        help_text="Last attended school/college (optional).",
    )
    ssc_gpa = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True,
        help_text="Secondary exam GPA (or equivalent), if applicable.",
    )

    photo = models.ImageField(
        upload_to="admissions/photos/", blank=True, null=True,
        help_text="Passport-size photo (optional in demo).",
    )
    transcript = models.FileField(
        upload_to="admissions/transcripts/", blank=True, null=True,
        help_text="Academic transcript/certificate (optional).",
    )
    message = models.TextField(
        blank=True,
        help_text="Any additional information or questions.",
    )

    # Chosen add-ons
    add_bus = models.BooleanField(
        default=False,
        help_text="Applicant opts for transport service.",
    )
    add_hostel = models.BooleanField(
        default=False,
        help_text="Applicant opts for hostel/accommodation.",
    )
    add_marksheet = models.BooleanField(
        default=False,
        help_text="Applicant opts for marksheet/certification processing.",
    )

    # Base rows (allow toggling in UI)
    add_admission = models.BooleanField(
        default=False,
        help_text="Include Admission fee row in snapshot.",
    )
    add_tuition = models.BooleanField(
        default=False,
        help_text="Include First Month Tuition row in snapshot.",
    )
    add_exam = models.BooleanField(
        default=False,
        help_text="Include Exam fee row in snapshot.",
    )

    # Fee snapshot (copied from Course at the time of submit)
    fee_admission = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Snapshot of admission fee at submit time.",
    )
    fee_tuition = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Snapshot of first-month tuition at submit time.",
    )
    fee_exam = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Snapshot of exam fee at submit time.",
    )
    fee_bus = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Snapshot of transport fee at submit time.",
    )
    fee_hostel = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Snapshot of hostel fee at submit time.",
    )
    fee_marksheet = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Snapshot of marksheet fee at submit time.",
    )

    fee_base_subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Admission + First Month Tuition + Exam (if chosen).",
    )
    fee_selected_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Total of all selected rows (base + add-ons).",
    )

    # legacy compatibility
    fee_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Legacy total; prefer fee_selected_total.",
    )

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default="pending",
        help_text="Status of the application payment, if any.",
    )
    payment_provider = models.CharField(
        max_length=30, blank=True,
        help_text="e.g., 'paypal', 'bkash' (set when payment succeeds).",
    )
    payment_txn_id = models.CharField(
        max_length=100, blank=True,
        help_text="Gateway transaction/capture ID.",
    )
    paid_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp recorded when payment_status becomes Paid.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this application was submitted.",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Admission Application"
        verbose_name_plural = "Admission Applications"

    def __str__(self):
        return f"{self.full_name} — {self.desired_course}"

    # helper
    def mark_paid(self, provider: str, txn_id: str):
        """
        Mark the application as paid and persist provider + transaction id.
        """
        self.payment_provider = provider
        self.payment_txn_id = txn_id
        self.payment_status = "paid"
        self.paid_at = timezone.now()
        self.save(update_fields=["payment_provider", "payment_txn_id", "payment_status", "paid_at"])


# ---------- Function Highlights ----------

class FunctionHighlight(models.Model):
    """
    A single highlight block for college functions/events.
    One image per item; provides a simple alternating left/right layout on the homepage.
    """
    title = models.CharField(
        max_length=200,
        help_text="Headline for the function highlight (shown over the image).",
    )
    image = models.ImageField(
        upload_to="functions/",
        help_text="Primary image for this highlight.",
    )
    place = models.CharField(
        max_length=200, blank=True,
        help_text="Venue/location (optional).",
    )
    date_text = models.CharField(
        max_length=120, blank=True,
        help_text="Human-friendly date (e.g., 'December 20, 2025').",
    )
    time_text = models.CharField(
        max_length=120, blank=True,
        help_text="Human-friendly time (e.g., '4:00 PM onwards').",
    )
    description = models.TextField(
        blank=True,
        help_text="Short description shown beside the image.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this highlight from the site.",
    )

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "Function Highlight"
        verbose_name_plural = "Function Highlights"

    def __str__(self):
        return self.title

    @property
    def image_src(self):
        """Return a safe URL for the image (empty string if unavailable)."""
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return ""


# ---------- College Festivals ----------

class CollegeFestival(models.Model):
    """
    A festival page/card containing an optional hero (image/video/YouTube),
    description, and a gallery of media items (see FestivalMedia).
    """
    title = models.CharField(
        max_length=200,
        help_text="Festival title as shown on cards and headers.",
    )
    slug = models.SlugField(
        unique=True,
        help_text="Unique slug for links. Auto-fill from title if unsure.",
    )
    place = models.CharField(
        max_length=200, blank=True,
        help_text="Venue/location (optional).",
    )
    date_text = models.CharField(
        max_length=100, blank=True,
        help_text="Friendly date (e.g., 'Feb 15, 2025').",
    )
    time_text = models.CharField(
        max_length=100, blank=True,
        help_text="Friendly time (e.g., '6:00 PM onwards').",
    )
    description = models.TextField(
        blank=True,
        help_text="Festival summary/notes.",
    )

    # Optional hero
    hero_image = models.ImageField(
        upload_to="festivals/hero/", blank=True, null=True,
        help_text="Hero image for the festival card/header (optional).",
    )
    hero_video = models.FileField(
        upload_to="festivals/video/", blank=True, null=True,
        help_text="Upload an MP4 (or similar) to play in modal (optional).",
    )
    hero_youtube_url = models.URLField(
        blank=True,
        help_text="Paste any YouTube link (watch/shorts/embed/youtu.be).",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this festival.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first across all festivals.",
    )

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="festivals_created",
        help_text="User who created this record (optional).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this festival record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this festival record was last updated.",
    )

    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "College Festival"
        verbose_name_plural = "College Festivals"

    def __str__(self):
        return self.title


class FestivalMedia(models.Model):
    """
    A single media item belonging to a CollegeFestival.
    Supports both images and YouTube links with an optional custom thumbnail.
    """
    KIND_CHOICES = (
        ("image", "Image"),
        ("youtube", "YouTube"),
    )

    festival = models.ForeignKey(
        CollegeFestival, on_delete=models.CASCADE, related_name="media_items",
        help_text="Festival this media belongs to.",
    )
    kind = models.CharField(
        max_length=20, choices=KIND_CHOICES, default="image",
        help_text="Choose 'Image' for uploads or 'YouTube' for embedded videos.",
    )

    image = models.ImageField(
        upload_to="festivals/gallery/", blank=True, null=True,
        help_text="Upload the image (required if kind=Image).",
    )
    youtube_url = models.URLField(
        blank=True,
        help_text="Paste any YouTube link (required if kind=YouTube).",
    )

    thumbnail = models.ImageField(
        upload_to="festivals/thumbs/", blank=True, null=True,
        help_text="Optional thumbnail (otherwise we try to display the original).",
    )

    caption = models.CharField(
        max_length=200, blank=True,
        help_text="Short caption or credit for the media item.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first within the festival gallery.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this media item.",
    )

    class Meta:
        ordering = ("order", "id")
        verbose_name = "Festival Media"
        verbose_name_plural = "Festival Media"

    def __str__(self):
        base = self.caption or (self.image.name if self.image else self.youtube_url) or "item"
        return f"{self.festival.title} – {base}"


# ---------- People ----------

class Member(models.Model):
    """
    People directory for the site: HOD, Teachers, Students, and Staff.
    You can optionally supply a hosted image via 'photo_url' if 'photo' is empty.
    """

    class Role(models.TextChoices):
        HOD = "hod", "Head of Department"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"
        STAFF = "staff", "Staff"

    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this member from listings.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first within the same role.",
    )

    role = models.CharField(
        max_length=20, choices=Role.choices,
        help_text="Which group this member belongs to.",
    )
    name = models.CharField(
        max_length=120,
        help_text="Full display name.",
    )
    post = models.CharField(
        max_length=120, blank=True,
        help_text="Designation/position (e.g., Professor, Lab Assistant).",
    )
    section = models.CharField(
        max_length=10, blank=True,
        help_text="Student section if relevant (e.g., 'A').",
    )
    bio = models.TextField(
        blank=True,
        help_text="Short bio/intro (optional, shown in detail cards).",
    )

    photo = models.ImageField(
        upload_to="members/", blank=True, null=True,
        help_text="Upload a headshot (square images look best).",
    )
    photo_url = models.URLField(
        blank=True,
        help_text="Remote image URL if you prefer not to upload.",
    )

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="members_created",
        help_text="User who created this record (optional).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this profile was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this profile was last updated.",
    )

    class Meta:
        ordering = ("order", "name")
        verbose_name = "Member"
        verbose_name_plural = "Members"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    @property
    def image_src(self):
        """Return the best available image URL (uploaded photo, else photo_url, else empty)."""
        try:
            if self.photo and self.photo.url:
                return self.photo.url
        except Exception:
            pass
        return self.photo_url or ""


# ---------- Contact ----------

class ContactInfo(models.Model):
    """
    Single source of truth for the Contact section of your site.
    Add one active record; the latest active one is shown on the homepage.
    """
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to stop showing this record on the site.",
    )
    address = models.CharField(
        max_length=255, blank=True,
        help_text="Street address and city/district.",
    )
    phone = models.CharField(
        max_length=100, blank=True,
        help_text="Primary phone number (can include multiple, separated by commas).",
    )
    email = models.EmailField(
        blank=True,
        help_text="Public contact email.",
    )
    hours = models.CharField(
        max_length=255, blank=True,
        help_text="Opening hours (e.g., 'Mon–Sat: 8:00 AM – 5:00 PM').",
    )
    map_embed_src = models.TextField(
        blank=True,
        help_text="Paste a Google Maps <iframe> src URL or an embeddable map URL.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated.",
    )

    class Meta:
        verbose_name = "Contact Info"
        verbose_name_plural = "Contact Info"

    def __str__(self):
        return f"Contact Info ({'active' if self.is_active else 'inactive'})"


class ContactMessage(models.Model):
    """
    Messages submitted from the site contact form. Use the 'handled' flag to
    mark messages as processed in the admin.
    """
    name = models.CharField(
        max_length=120,
        help_text="Sender’s name.",
    )
    email = models.EmailField(
        help_text="Sender’s email address.",
    )
    subject = models.CharField(
        max_length=200,
        help_text="Short subject line for the message.",
    )
    message = models.TextField(
        help_text="The user’s message or inquiry.",
    )
    phone = models.CharField(
        max_length=50, blank=True,
        help_text="Optional phone number for follow-up.",
    )
    website = models.CharField(
        max_length=200, blank=True,
        help_text="Honeypot anti-spam (should stay empty for humans).",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this message was received.",
    )
    handled = models.BooleanField(
        default=False,
        help_text="Tick when the message has been replied to/resolved.",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.subject[:40]}"


# ---------- Footer ----------

class FooterSettings(models.Model):
    """
    Global footer configuration. Create/keep one active record; the latest active
    one is rendered on the site. Lets non-technical admins control links, socials,
    and branding without touching templates.
    """
    is_active = models.BooleanField(
        default=True,
        help_text="Only active records are considered on the website.",
    )
    title = models.CharField(
        max_length=120, default="Titu BD Science College",
        help_text="Display title/brand next to contact info.",
    )

    # Contact block
    address = models.CharField(
        max_length=255, blank=True,
        help_text="Footer contact address.",
    )
    phone = models.CharField(
        max_length=120, blank=True,
        help_text="Footer phone (can include multiple, separated by commas).",
    )
    email = models.EmailField(
        blank=True,
        help_text="Footer email address.",
    )

    # Quick links
    link_home_enabled = models.BooleanField(
        default=True,
        help_text="Include the Home link.",
    )
    link_admission_label = models.CharField(
        max_length=80, default="Admission",
        help_text="Text label for the Admission link.",
    )
    link_admission_url = models.URLField(
        blank=True,
        help_text="URL to your admission page/form.",
    )
    link_results_label = models.CharField(
        max_length=80, default="Results",
        help_text="Text label for the Results link.",
    )
    link_results_url = models.URLField(
        blank=True,
        help_text="URL to your results portal/page.",
    )
    link_events_label = models.CharField(
        max_length=80, default="Events (Highlights)",
        help_text="Text label for the Events anchor link.",
    )
    link_events_anchor = models.CharField(
        max_length=120, default="#college-functions",
        help_text="Anchor or URL to your events/highlights section.",
    )

    # Socials
    facebook_url = models.URLField(
        blank=True,
        help_text="Link to your Facebook page.",
    )
    whatsapp_url = models.URLField(
        blank=True,
        help_text="Link to your WhatsApp (group/business/profile).",
    )
    twitter_url = models.URLField(
        blank=True,
        help_text="Link to your Twitter/X profile.",
    )
    email_linkto = models.EmailField(
        blank=True,
        help_text="Different contact email for the mail icon (defaults to footer email).",
    )

    # Branding
    logo = models.ImageField(
        upload_to="footer/", blank=True, null=True,
        help_text="Footer brand/logo image (small).",
    )
    logo_url = models.URLField(
        blank=True,
        help_text="Remote logo URL if you don't want to upload a file.",
    )

    # Credits / copyright
    copyright_name = models.CharField(
        max_length=160, default="Titu BD Science College",
        help_text="Name displayed in copyright line.",
    )
    developer_name = models.CharField(
        max_length=160, default="DS",
        help_text="Developer/vendor credit name.",
    )
    developer_url = models.URLField(
        blank=True, default="https://t2bd.com",
        help_text="Link for the developer credit.",
    )

    # Audit
    created_by = models.ForeignKey(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="footer_settings_created",
        help_text="User who created this footer config (optional).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this footer record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this footer record was last updated.",
    )

    class Meta:
        verbose_name = "Footer Settings"
        verbose_name_plural = "Footer Settings"

    def __str__(self):
        return f"Footer: {self.title} (active={self.is_active})"

    @property
    def logo_src(self) -> str:
        """Return a usable logo URL (uploaded file wins; fallback to remote URL)."""
        try:
            if self.logo and self.logo.url:
                return self.logo.url
        except Exception:
            pass
        return self.logo_url or ""






def gallery_upload_image_to(instance, filename):
    dt = timezone.now()
    return f"gallery/images/{dt:%Y/%m}/{filename}"

def gallery_upload_video_to(instance, filename):
    dt = timezone.now()
    return f"gallery/videos/{dt:%Y/%m}/{filename}"

class GalleryPost(models.Model):
    KIND_IMAGE  = "image"
    KIND_VIDEO  = "video"
    KIND_YT     = "youtube"
    KIND_CHOICES = [
        (KIND_IMAGE, "Image"),
        (KIND_VIDEO, "Video (MP4)"),
        (KIND_YT,    "YouTube URL"),
    ]

    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    kind        = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_IMAGE)

    title       = models.CharField(max_length=200)
    # one of the following depending on kind
    image       = models.ImageField(upload_to=gallery_upload_image_to, blank=True, null=True)
    video       = models.FileField(upload_to=gallery_upload_video_to, blank=True, null=True)   # e.g. .mp4
    youtube_url = models.URLField(blank=True)

    created_by  = models.ForeignKey(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        null=True, blank=True, on_delete=models.SET_NULL, related_name="gallery_posts_created"
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "-created_at")

    def __str__(self):
        return self.title

    @property
    def thumb_src(self) -> str:
        """
        For image: the image URL.
        For video: use the video tag (no thumb) — template shows a play badge.
        For YouTube: try to render the standard thumbnail.
        """
        if self.kind == self.KIND_IMAGE and self.image:
            try:
                return self.image.url
            except Exception:
                return ""
        if self.kind == self.KIND_YT and self.youtube_id:
            # default thumbnail
            return f"https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg"
        return ""

    @property
    def youtube_id(self) -> str:
        """
        Extract a video ID from common YouTube URL shapes (watch, youtu.be, shorts, embed).
        """
        import re
        url = (self.youtube_url or "").strip()
        if not url:
            return ""
        # patterns: youtu.be/ID, v=ID, /embed/ID, /shorts/ID
        for pat in [
            r"youtu\.be/([A-Za-z0-9_-]{6,})",
            r"[?&]v=([A-Za-z0-9_-]{6,})",
            r"/embed/([A-Za-z0-9_-]{6,})",
            r"/shorts/([A-Za-z0-9_-]{6,})",
        ]:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return ""






class AcademicClass(models.Model):
    name = models.CharField(
        max_length=80,
        help_text='Class name as shown to users, e.g. "Class 8" or "Grade 10".'
    )
    section = models.CharField(
        max_length=20,
        blank=True,
        help_text='Optional section/stream label, e.g. "A", "Science". Leave empty if not used.'
    )
    year = models.PositiveIntegerField(
        default=timezone.now().year,
        help_text="Academic year for this class (e.g., 2025)."
    )

    class Meta:
        unique_together = ("name", "section", "year")
        ordering = ("-year", "name", "section")

    def __str__(self):
        return f"{self.name}{' - ' + self.section if self.section else ''} ({self.year})"


class Subject(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Short code for the subject, e.g. "ENG", "MATH". Must be unique.'
    )
    title = models.CharField(
        max_length=120,
        help_text='Full subject title as shown to users, e.g. "English", "Mathematics".'
    )

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} — {self.title}"


class ExamTerm(models.Model):
    name = models.CharField(
        max_length=80,
        help_text='Exam term name, e.g. "Midterm", "Final", "Term 1".'
    )
    year = models.PositiveIntegerField(
        default=timezone.now().year,
        help_text="Calendar year of the exam term (e.g., 2025)."
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional date when the exam term starts (for reference)."
    )

    class Meta:
        unique_together = ("name", "year")
        ordering = ("-year", "name")

    def __str__(self):
        return f"{self.name} {self.year}"


class ClassResultSummary(models.Model):
    """
    One row per (Class, Term) with class-level aggregates only.
    """
    klass = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
        related_name="result_summaries",
        help_text="Which class these results belong to."
    )
    term = models.ForeignKey(
        ExamTerm,
        on_delete=models.CASCADE,
        related_name="result_summaries",
        help_text="Which exam term these results summarize."
    )

    total_students = models.PositiveIntegerField(
        default=0,
        help_text="Total students enrolled in the class."
    )
    appeared = models.PositiveIntegerField(
        default=0,
        help_text="Number of students who appeared for the exam in this term."
    )
    pass_rate_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pass percentage for the class (0–100)."
    )
    overall_avg_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall average percentage for the class (0–100)."
    )
    highest_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Highest percentage achieved in the class (0–100)."
    )
    lowest_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Lowest percentage achieved in the class (0–100)."
    )
    remarks = models.TextField(
        blank=True,
        help_text="Optional notes or remarks shown on the class result page."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this summary was created (auto)."
    )

    class Meta:
        unique_together = ("klass", "term")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.klass} — {self.term}"


class ClassResultSubjectAvg(models.Model):
    """
    Optional per-subject class averages.
    """
    summary = models.ForeignKey(
        ClassResultSummary,
        on_delete=models.CASCADE,
        related_name="subject_avgs",
        help_text="Select the (Class, Term) summary this average belongs to."
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="class_avgs",
        help_text="Subject for which you are recording the class average."
    )
    avg_score = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Average marks the class scored in this subject."
    )
    out_of = models.PositiveIntegerField(
        default=100,
        help_text="Maximum possible marks for this subject average (e.g., 100)."
    )

    class Meta:
        unique_together = ("summary", "subject")
        ordering = ("subject__code",)

    def __str__(self):
        return f"{self.summary} — {self.subject.code}"

    @property
    def avg_pct(self) -> float:
        try:
            return round(float(self.avg_score) / float(self.out_of) * 100.0, 2)
        except Exception:
            return 0.0


def upload_student_profile_to(instance, filename):
    dt = timezone.now()
    return f"students/profiles/{dt:%Y/%m}/{filename}"


class ClassTopper(models.Model):
    """
    Toppers for a given class+term summary. No per-student subject rows—just the essentials.
    """
    summary = models.ForeignKey(
        ClassResultSummary,
        on_delete=models.CASCADE,
        related_name="toppers",
        help_text="Select the (Class, Term) summary this topper belongs to."
    )
    rank = models.PositiveIntegerField(
        default=1,
        help_text="Rank in the class for this term (1 = topper)."
    )
    name = models.CharField(
        max_length=120,
        help_text="Student full name as it should appear on the site."
    )
    roll_no = models.CharField(
        max_length=40,
        blank=True,
        help_text="Optional roll number / ID for reference."
    )
    profile_image = models.ImageField(
        upload_to=upload_student_profile_to,
        blank=True, null=True,
        help_text="Optional student profile photo (square crop recommended)."
    )

    total_pct = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Overall % (e.g., 92.50)."
    )
    grade = models.CharField(
        max_length=8,
        blank=True,
        help_text='Optional grade label, e.g., "A+", "A".'
    )

    class Meta:
        unique_together = ("summary", "rank")
        ordering = ("rank", "id")

    def __str__(self):
        return f"{self.summary} — Rank {self.rank}: {self.name}"






# Use the model labels from settings (e.g., "school.Class")
CLASS_MODEL_LABEL   = getattr(settings, "ATTENDANCE_CLASS_MODEL",   "academics.Classroom")
STUDENT_MODEL_LABEL = getattr(settings, "ATTENDANCE_STUDENT_MODEL", "students.Student")

class AttendanceSession(models.Model):
    """
    One class on one calendar date (counts only; no per-student rows).
    Unique per (class, date).
    """
    school_class = models.ForeignKey(
        "content.AcademicClass",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    date        = models.DateField(default=timezone.localdate)
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    notes       = models.CharField(max_length=255, blank=True)

    # ---- COUNT FIELDS (class-wise) ----
    present_count = models.PositiveIntegerField(default=0)
    absent_count  = models.PositiveIntegerField(default=0)
    late_count    = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school_class", "date"],
                name="uniq_class_day_session",
            ),
        ]
        indexes = [
            models.Index(fields=["school_class", "date"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.school_class} – {self.date}"

    # Convenience properties (nice for admin / templates)
    @property
    def total_count(self) -> int:
        return (self.present_count or 0) + (self.absent_count or 0) + \
               (self.late_count or 0) + (self.excused_count or 0)

    @property
    def attendance_rate_pct(self) -> float:
        total = self.total_count
        if not total:
            return 0.0
        # Excused counts as non-absent
        return round(100.0 * ((self.present_count or 0) + (self.excused_count or 0)) / total, 1)











class ExamRoutine(models.Model):
    """
    A published exam routine image for a given class and term/semester, with exam dates.
    """
    is_active = models.BooleanField(default=True)

    school_class = models.ForeignKey(
        "content.AcademicClass",
        on_delete=models.CASCADE,
        related_name="exam_routines",
    )
    term = models.ForeignKey(
        "content.ExamTerm",
        on_delete=models.CASCADE,
        related_name="exam_routines",
    )

    title = models.CharField(max_length=160, blank=True)
    routine_image = models.ImageField(upload_to="exam_routines/%Y/%m/", blank=True, null=True)
    routine_image_url = models.URLField(blank=True, default="")  # fallback if you prefer linking

    exam_start_date = models.DateField()
    exam_end_date = models.DateField(blank=True, null=True)  # optional (single-day if empty)
    notes = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-exam_start_date", "-id")
        constraints = [
            models.CheckConstraint(
                name="exam_date_range_valid",
                check=Q(exam_end_date__gte=F("exam_start_date")) | Q(exam_end_date__isnull=True),
            )
        ]

    def __str__(self):
        base = self.title or f"{self.school_class} — {self.term}"
        if self.exam_end_date and self.exam_end_date != self.exam_start_date:
            return f"{base} ({self.exam_start_date} → {self.exam_end_date})"
        return f"{base} ({self.exam_start_date})"

    @property
    def image_src(self) -> str:
        """Prefer uploaded image, fall back to URL."""
        try:
            if self.routine_image and self.routine_image.url:
                return self.routine_image.url
        except Exception:
            pass
        return self.routine_image_url or ""
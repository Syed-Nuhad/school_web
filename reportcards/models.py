from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


def current_year():
    return timezone.now().year


# -----------------------------
# Core catalog
# -----------------------------
class Grade(models.Model):
    """
    e.g. name='Class 10', section='A', year=2025
    """
    name = models.CharField(max_length=80)
    section = models.CharField(max_length=20, blank=True)
    year = models.PositiveIntegerField(default=current_year)

    class Meta:
        unique_together = (("name", "section", "year"),)
        ordering = ("-year", "name", "section")

    def __str__(self):
        sec = f" - {self.section}" if self.section else ""
        return f"{self.name}{sec} ({self.year})"


class GradeSubject(models.Model):
    """
    A subject that belongs to a Grade, e.g. (Class 10) → Math, English...
    """
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="subjects")
    name = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("grade", "name"),)
        ordering = ("grade", "order", "name")

    def __str__(self):
        return self.name


class Term(models.Model):
    """
    e.g. name='First Term', year=2025
    """
    name = models.CharField(max_length=80)
    year = models.PositiveIntegerField(default=current_year)

    class Meta:
        unique_together = (("name", "year"),)
        ordering = ("-year", "name")

    def __str__(self):
        return f"{self.name} {self.year}"


# -----------------------------
# Marksheet + rows
# -----------------------------
def _letter_and_gpa(percent: float) -> tuple[str, Decimal]:
    """Bangladesh-style scale (adjust if you need)."""
    p = float(percent or 0)
    if p >= 80:  return "A+", Decimal("5.00")
    if p >= 70:  return "A",  Decimal("4.00")
    if p >= 60:  return "A-", Decimal("3.50")
    if p >= 50:  return "B",  Decimal("3.00")
    if p >= 40:  return "C",  Decimal("2.00")
    if p >= 33:  return "D",  Decimal("1.00")
    return "F", Decimal("0.00")


class Marksheet(models.Model):
    grade      = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="marksheets")
    term       = models.ForeignKey(Term,  on_delete=models.PROTECT, related_name="marksheets")

    student_name = models.CharField(max_length=200)
    roll_number  = models.CharField(max_length=50, blank=True, default="")
    section      = models.CharField(max_length=50, blank=True, default="")
    notes        = models.TextField(blank=True, default="")

    # Auto-computed fields
    total_obtained = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    total_out_of   = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    percent        = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    grade_letter   = models.CharField(max_length=4, blank=True, default="")
    gpa            = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        unique_together = (("grade", "term", "student_name", "roll_number"),)
        ordering = ("-updated_at", "student_name")

    def __str__(self):
        return f"{self.student_name} — {self.grade} — {self.term}"

    def recalc_totals(self):
        rows = list(self.rows.all())
        obtained = sum((r.marks_obtained or 0) for r in rows)
        out_of   = sum((r.max_marks or 0) for r in rows)
        pct      = (float(obtained) / float(out_of) * 100.0) if out_of else 0.0
        letter, gpa = _letter_and_gpa(pct)

        self.total_obtained = Decimal(obtained)
        self.total_out_of   = Decimal(out_of)
        self.percent        = Decimal(f"{pct:.2f}")
        self.grade_letter   = letter
        self.gpa            = gpa
        return self.total_obtained


class MarkRow(models.Model):
    """
    One row per subject on the marksheet.
    """
    marksheet = models.ForeignKey(Marksheet, on_delete=models.CASCADE, related_name="rows")
    subject   = models.ForeignKey(GradeSubject, on_delete=models.PROTECT, related_name="rows")

    max_marks      = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("100.00"))
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))

    grade_letter = models.CharField(max_length=5, blank=True, default="")
    remark       = models.CharField(max_length=200, blank=True, default="")
    order        = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("marksheet", "subject"),)
        ordering = ("order", "id")

    def __str__(self):
        return self.subject.name if self.subject_id else "Row"

    def save(self, *args, **kwargs):
        # compute letter from this row's percentage
        try:
            maxm = float(self.max_marks or 0)
            got = float(self.marks_obtained or 0)
            pct = (got / maxm * 100.0) if maxm > 0 else 0.0
        except Exception:
            pct = 0.0
        letter, _gpa = _letter_and_gpa(pct)
        self.grade_letter = letter
        super().save(*args, **kwargs)

    def clean(self):
        if self.subject_id and self.marksheet_id:
            if self.subject.grade_id != self.marksheet.grade_id:
                raise ValidationError("Subject must belong to the same Grade as the Marksheet.")


# -----------------------------
# Keep totals in sync automatically
# -----------------------------
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=MarkRow)
def _recalc_parent(sender, instance, **kwargs):
    ms = instance.marksheet
    ms.recalc_totals()
    ms.save(update_fields=[
        "total_obtained", "total_out_of", "percent", "grade_letter", "gpa", "updated_at"
    ])

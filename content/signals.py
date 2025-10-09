# content/signals.py
from io import BytesIO

from django.core.files.base import ContentFile
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ✅ new helper name
from .billing import ensure_monthly_window_for_user
from .models import StudentMarksheetItem, TuitionPayment, PaymentReceipt, StudentProfile


# ---------- Marksheet totals ----------
@receiver([post_save, post_delete], sender=StudentMarksheetItem)
def recalc_marksheet_totals(sender, instance, **kwargs):
    ms = instance.marksheet
    ms.recalc_totals()
    ms.save(update_fields=["total_marks", "total_grade", "updated_at"])


# ---------- Tuition payment → PDF receipt ----------
@receiver(post_save, sender=TuitionPayment)
def make_receipt_for_tuition(sender, instance: TuitionPayment, created, **kwargs):
    if not created:
        return
    # Idempotency: skip if a receipt already exists for this txn
    if PaymentReceipt.objects.filter(txn_id=instance.txn_id).exists():
        return

    student = instance.invoice.student

    # Build a tiny A4 receipt PDF
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "Payment Receipt")
    p.setFont("Helvetica", 12)
    p.drawString(60, 760, f"Student: {student.get_full_name() or student.username}")
    p.drawString(60, 740, f"Amount Paid: BDT {instance.amount}")
    p.drawString(60, 720, f"Provider: {(instance.provider or '').title()}")
    p.drawString(60, 700, f"Transaction ID: {instance.txn_id}")
    p.drawString(60, 680, f"Date: {timezone.localdate()}")
    p.drawString(60, 660, "Thank you for your payment.")
    p.showPage()
    p.save()
    pdf_buffer.seek(0)

    receipt = PaymentReceipt.objects.create(
        student=student,
        payment=instance,
        amount=instance.amount,
        provider=instance.provider,
        txn_id=instance.txn_id,
    )
    receipt.pdf.save(f"receipt_{receipt.id}.pdf", ContentFile(pdf_buffer.read()))


# ---------- Ensure monthly invoices ----------

User = get_user_model()

@receiver(post_save, sender=User)
def _ensure_monthly_on_user_create(sender, instance: User, created, **kwargs):
    """When a user is created, create the monthly invoice window if applicable."""
    if created:
        try:
            ensure_monthly_window_for_user(instance)
        except Exception:
            # Never block startup/migrations
            pass


@receiver(post_save, sender=StudentProfile)
def _ensure_monthly_on_profile_link(sender, instance: StudentProfile, created, **kwargs):
    """
    When a student profile is created or (first) linked to a user,
    ensure this month’s invoice window exists.
    """
    if instance.user_id:
        try:
            ensure_monthly_window_for_user(instance.user)
        except Exception:
            pass

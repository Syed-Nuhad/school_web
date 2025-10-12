# ========= START: finance/services/receipts.py =========
from io import BytesIO
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils import timezone

try:
    from weasyprint import HTML
    WEASY_AVAILABLE = True
except Exception:
    WEASY_AVAILABLE = False

from ..models import PaymentReceipt, TuitionPayment

def generate_payment_receipt(payment: TuitionPayment) -> PaymentReceipt:
    context = {"payment": payment}
    try:
        html = render_to_string("finance/receipt_pdf.html", context)
    except Exception:
        html = f"""
        <html><body>
          <h2>Payment Receipt</h2>
          <p>Payment ID: {payment.id}</p>
          <p>Gateway: {payment.gateway or ''}</p>
          <p>Reference: {payment.gateway_ref or ''}</p>
          <p>Payer Email: {payment.gateway_payer_email or ''}</p>
          <p>Amount: {getattr(payment, 'amount', '')}</p>
          <p>Paid At: {payment.paid_at or timezone.now()}</p>
        </body></html>
        """

    receipt = PaymentReceipt.objects.create(payment=payment)

    try:
        from weasyprint import HTML  # lazy import
        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        receipt.pdf.save(f"receipt-{payment.id}.pdf", ContentFile(pdf_io.getvalue()), save=True)
    except Exception:
        receipt.save(update_fields=["created_at"])
    return receipt
# ========= END: finance/services/receipts.py =========

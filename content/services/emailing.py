from __future__ import annotations
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def send_email_smtp(*, to: str, subject: str, body_text: str, body_html: str | None = None, from_email: str | None = None, reply_to: str | None = None) -> str:
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    reply_to_list = [reply_to or settings.EMAIL_REPLY_TO] if (reply_to or getattr(settings, "EMAIL_REPLY_TO", None)) else None
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text or "",
        from_email=from_email,
        to=[to],
        reply_to=reply_to_list,
    )
    if body_html:
        msg.attach_alternative(body_html, "text/html")
    msg_id = msg.send(fail_silently=False)
    # Django's SMTP backend doesn't expose Message-Id directly; store int return
    return str(msg_id)  # best-effort

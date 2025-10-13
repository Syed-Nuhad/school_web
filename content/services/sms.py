from __future__ import annotations
import requests
from django.conf import settings

class SmsSendError(Exception):
    pass

def send_sms_generic(*, to: str, sender_id: str, body: str) -> str:
    """
    Example generic HTTP gateway:
    expects base URL and api_key in settings. Returns provider reference/id.
    """
    base = settings.SMS_GENERIC_BASE_URL
    key  = settings.SMS_GENERIC_API_KEY
    payload = {"to": to, "sender": sender_id, "message": body, "api_key": key}
    resp = requests.post(base, json=payload, timeout=15)
    if resp.status_code // 100 != 2:
        raise SmsSendError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json() if resp.headers.get("content-type","").startswith("application/json") else {}
    return str(data.get("message_id") or data.get("id") or "")

# Optional: Twilio
def send_sms_twilio(*, to: str, sender_id: str, body: str) -> str:
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        to=to,
        from_=settings.TWILIO_FROM_NUMBER or sender_id,
        body=body
    )
    return msg.sid

def send_sms(*, to: str, sender_id: str, body: str) -> tuple[str, str]:
    """
    Returns (provider, provider_ref)
    """
    provider = settings.SMS_PROVIDER.lower()
    if provider == "twilio":
        ref = send_sms_twilio(to=to, sender_id=sender_id, body=body)
        return "twilio", ref
    else:
        ref = send_sms_generic(to=to, sender_id=sender_id, body=body)
        return "generic", ref

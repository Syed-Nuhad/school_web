from django.core.management.base import BaseCommand
from django.conf import settings
from content.services.comms_outbox import process_sms_batch, process_email_batch

class Command(BaseCommand):
    help = "Send queued SMS and Email from Outbox."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--only", choices=["sms","email","both"], default="both")

    def handle(self, *args, **opts):
        limit = opts["limit"]
        only = opts["only"]
        total = 0
        if only in ("sms", "both"):
            sent = process_sms_batch(limit=limit)
            self.stdout.write(self.style.SUCCESS(f"SMS sent: {sent}"))
            total += sent
        if only in ("email", "both"):
            sent = process_email_batch(limit=limit)
            self.stdout.write(self.style.SUCCESS(f"Email sent: {sent}"))
            total += sent
        self.stdout.write(self.style.SUCCESS(f"Total processed: {total}"))

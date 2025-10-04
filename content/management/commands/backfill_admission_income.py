# ===== START: management command =====
from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import AdmissionApplication, Income
from content.models import _admission_income_line_items, _admission_has_income_already  # reuse helpers

class Command(BaseCommand):
    help = "Create Income rows for already-paid AdmissionApplications that have none."

    def handle(self, *args, **options):
        count_created = 0
        qs = AdmissionApplication.objects.filter(payment_status="paid")
        for app in qs:
            if _admission_has_income_already(app):
                continue
            lines = _admission_income_line_items(app)
            if not lines:
                continue
            stamp = app.paid_at.date() if app.paid_at else timezone.localdate()
            for source, amount, label in lines:
                Income.objects.create(
                    source=source,
                    amount=amount,
                    date=stamp,
                    description=(
                        f"{label} — Applicant: {app.full_name} "
                        f"({app.desired_course or 'Course'}) | "
                        f"Provider: {app.payment_provider or 'n/a'} | TXN:{app.payment_txn_id or 'n/a'}"
                    )
                )
                count_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {count_created} Income rows."))
# ===== END: management command =====

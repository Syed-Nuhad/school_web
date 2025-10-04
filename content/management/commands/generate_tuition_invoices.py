# ===== START: generate_tuition_invoices.py =====
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from content.models import TuitionInvoice

class Command(BaseCommand):
    help = (
        "Generate monthly TuitionInvoice rows for students.\n"
        "Usage: manage.py generate_tuition_invoices --year 2025 --month 10 --amount 2000 "
        "[--only-missing]"
    )

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True)
        parser.add_argument("--month", type=int, required=True)
        parser.add_argument("--amount", type=float, required=True,
                            help="Tuition amount per student (BDT).")
        parser.add_argument("--only-missing", action="store_true",
                            help="Only create invoices that don't already exist.")

    def handle(self, *args, **opts):
        year  = opts["year"]
        month = opts["month"]
        amount = float(opts["amount"])
        only_missing = opts["only_missing"]

        # Pick your student set. If you have a 'Students' group, use it; else: all non-staff users.
        User = get_user_model()
        qs = User.objects.filter(is_active=True, is_staff=False)

        created = 0
        for u in qs.iterator():
            if only_missing and TuitionInvoice.objects.filter(
                student=u, period_year=year, period_month=month
            ).exists():
                continue

            inv, made = TuitionInvoice.objects.get_or_create(
                student=u, period_year=year, period_month=month,
                defaults={
                    "tuition_amount": amount,
                    "due_date": timezone.localdate().replace(year=year, month=month, day=10),
                    "notes": "Auto-generated",
                }
            )
            if made:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} invoices for {year}-{month:02d}."))
# ===== END: generate_tuition_invoices.py =====

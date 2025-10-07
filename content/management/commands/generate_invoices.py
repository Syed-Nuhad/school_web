# content/management/commands/generate_invoices.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import StudentProfile, TuitionInvoice

class Command(BaseCommand):
    help = "Generate monthly tuition invoices for all students who don't have one for the given month."

    def add_arguments(self, parser):
        today = timezone.localdate()
        parser.add_argument("--year", type=int, default=today.year)
        parser.add_argument("--month", type=int, default=today.month)
        parser.add_argument("--amount", type=float, default=None,
                            help="Override amount for all students. If omitted, uses StudentProfile.monthly_fee (if present).")

    def handle(self, *args, **opts):
        year, month, override = opts["year"], opts["month"], opts["amount"]
        created = 0

        for sp in StudentProfile.objects.select_related("user", "school_class"):
            student = sp.user
            amount = override or getattr(sp, "monthly_fee", None)
            if not amount:
                continue

            _, was_created = TuitionInvoice.objects.get_or_create(
                student=student, period_year=year, period_month=month,
                defaults={"tuition_amount": amount}
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} invoice(s) for {year}-{month:02d}."))

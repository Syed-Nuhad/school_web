from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from content.models import StudentProfile, TuitionInvoice, FinanceSettings

User = get_user_model()

class Command(BaseCommand):
    help = "Ensure a monthly tuition invoice exists for all students for the given year/month (defaults to current)."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, help="Year, e.g. 2025")
        parser.add_argument("--month", type=int, help="Month 1-12")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        year  = opts.get("year") or today.year
        month = opts.get("month") or today.month

        fee = FinanceSettings.current().default_monthly_fee

        qs = StudentProfile.objects.select_related("user").exclude(user__isnull=True)
        created = 0
        for sp in qs:
            inv, was_created = TuitionInvoice.objects.get_or_create(
                student=sp.user,
                kind="monthly",
                period_year=year,
                period_month=month,
                defaults={
                    "tuition_amount": fee,
                    "paid_amount": 0,
                    "due_date": today.replace(day=min(25, 28)),
                    "title": "",
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} invoice(s) for {year}-{month:02d}."))

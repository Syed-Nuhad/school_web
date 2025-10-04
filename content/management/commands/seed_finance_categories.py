# =========================== START: Seeder Command ===========================
from django.core.management.base import BaseCommand
from content.models import IncomeCategory, ExpenseCategory

class Command(BaseCommand):
    help = "Seed built-in Finance categories."

    def handle(self, *args, **opts):
        income = [
            ("admission", "Admission Fee"),
            ("tuition", "Monthly Tuition"),
            ("bus", "Bus Service"),
            ("donation", "Donation/Other"),
        ]
        expense = [
            ("salary", "Salary"),
            ("fuel", "Fuel/Oil Purchase"),
            ("bus_repair", "Bus Repair"),
            ("bus_purchase", "Bus Purchase"),
            ("equip_purchase", "Equipment Purchase"),
            ("equip_repair", "Equipment Repair"),
            ("misc", "Miscellaneous"),
        ]
        for code, name in income:
            IncomeCategory.objects.get_or_create(code=code, defaults={"name": name, "is_fixed": True, "is_active": True})
        for code, name in expense:
            ExpenseCategory.objects.get_or_create(code=code, defaults={"name": name, "is_fixed": True, "is_active": True})
        self.stdout.write(self.style.SUCCESS("Finance categories seeded."))
# =========================== END: Seeder Command ===========================

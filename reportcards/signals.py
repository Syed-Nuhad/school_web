# reportcards/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from reportcards.models import MarkRow


@receiver([post_save, post_delete], sender=MarkRow)
def _recalc_parent(sender, instance, **kwargs):
    ms = instance.marksheet
    ms.recalc_totals()
    ms.save(update_fields=[
        "total_obtained", "total_out_of", "percent", "grade_letter", "gpa", "updated_at"
    ])

# content/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import StudentMarksheetItem

@receiver([post_save, post_delete], sender=StudentMarksheetItem)
def recalc_marksheet_totals(sender, instance, **kwargs):
    ms = instance.marksheet
    ms.recalc_totals()
    ms.save(update_fields=["total_marks", "total_grade", "updated_at"])

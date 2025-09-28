# reportcards/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver([post_save, post_delete], sender=MarkItem)
def _recalc_parent_totals(sender, instance, **kwargs):
    ms = instance.marksheet
    ms.recalc_totals()  # uses the method defined on your Marksheet model
    ms.save(update_fields=["total_marks", "total_percent", "gpa", "letter_grade", "updated_at"])

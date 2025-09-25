from content.models import FooterSettings


def footer_settings(request):
    """
    Makes `footer` available in all templates.
    Returns None if your settings row doesn't exist (template is guarded).
    """
    try:
        footer = FooterSettings.objects.first()
    except Exception:
        footer = None
    return {"footer": footer}


def default_class_id(request):
    # Prefer a class that actually has results; else any class.
    from content.models import AcademicClass, ClassResultSummary
    cid = (ClassResultSummary.objects
           .order_by("-term__year", "term__name", "klass__name")
           .values_list("klass_id", flat=True)
           .first())
    if not cid:
        cid = (AcademicClass.objects
               .order_by("-year", "name", "section")
               .values_list("id", flat=True)
               .first())
    return {"default_class_id": cid}
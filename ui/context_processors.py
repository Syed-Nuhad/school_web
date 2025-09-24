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
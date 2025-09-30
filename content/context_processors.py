from content.models import SiteBranding


def branding(request):
    """
    Injects BRAND into all templates: the latest active SiteBranding row,
    or None if not configured yet.
    """
    brand = (SiteBranding.objects
             .filter(is_active=True)
             .order_by("-updated_at", "-id")
             .first())
    if not brand:
        brand = SiteBranding.objects.order_by("-updated_at", "-id").first()
    return {"BRAND": brand}
from django.template import engines

django_engine = engines["django"]

def render_string(template_str: str, context: dict) -> str:
    if not template_str:
        return ""
    return django_engine.from_string(template_str).render(context)

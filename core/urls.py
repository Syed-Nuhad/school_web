# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from ui import views as ui_views
from accounts import views as acc_views  # for honeypots

urlpatterns = [
    # Public site
    path("", ui_views.home, name="home"),

    path("content/", include(("content.urls", "content"), namespace="content")),

    # Real Django admin (moved off /admin/)
    path("dj-admin/", admin.site.urls),

    # Accounts (public + secret prefixed inside accounts.urls)
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # ---- Honeypots at ROOT (decoys) ----
    path("admin/", acc_views.honeypot, name="hp_admin_root"),
    path("admin/login/", acc_views.honeypot, name="hp_admin_login"),
    path("teacher/login/", acc_views.honeypot, name="hp_teacher_login"),
    path("teacher/signup/", acc_views.honeypot, name="hp_teacher_signup"),
    path("notices/", ui_views.notices_list, name="notices_list"),
    path("notices/<int:pk>/", ui_views.notice_detail, name="notice_detail"),
]

# Serve static & media in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
    if getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

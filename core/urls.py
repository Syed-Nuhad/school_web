# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from ui import views as ui_views, views
from accounts import views as acc_views  # for honeypots
from ui.views import contact_submit, results_filter, results_detail

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
    path("admissions/", include("content.urls_admissions", namespace="admissions")),
    path("contact/submit/", contact_submit, name="contact_submit"),

    path("gallery/", views.gallery_page, name="gallery"),


    # 3) Class+term details (with toppers)
    # path("class/<int:klass_id>/term/<int:term_id>/", class_overview, name="class_overview"),
    path("results/", views.results_index, name="index"),
    path("results/filter/", views.results_filter, name="results_filter"),
    path("results/<int:summary_id>/", views.results_detail, name="results_detail"),

    # (optional) tiny debug endpoint you had
    path("results-debug/", views.results_debug, name="results_debug"),

    # ---------------------------
    # Attendance JSON (backend for the next UI step)
    # ---------------------------
    path("attendance/overview/<int:class_id>/",
         views.attendance_class_overview_json, name="attendance_class_overview_json"),
    path("attendance/day/<int:class_id>/",
         views.attendance_classday_get, name="attendance_classday_get"),
    path("attendance/day/upsert/",
         views.attendance_classday_upsert, name="attendance_classday_upsert"),
]


# Serve static & media in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
    if getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

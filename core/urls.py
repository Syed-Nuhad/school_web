# core/urls.py
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from content.admin import finance_overview_admin
from content.views import finance_export_csv, build_student_lookup_context
from ui import views as ui_views, views
from accounts import views as acc_views  # for honeypots
from ui.views import contact_submit, results_filter, results_detail, attendance_class_overview_json
import core.admin_menu


def student_lookup_admin(request):
    ctx = admin.site.each_context(request)
    ctx.update(build_student_lookup_context(request))
    ctx.setdefault("title", "Student Lookup")
    return TemplateResponse(request, "admin/students/lookup.html", ctx)




urlpatterns = [
    # Public site
    path("", ui_views.home, name="home"),

    path("content/", include(("content.urls", "content"), namespace="content")),

    # Real Django admin (moved off /admin/)
    path("dj-admin/finance/overview/", admin.site.admin_view(finance_overview_admin), name="finance-overview"),
    path("dj-admin/finance/export.csv",  admin.site.admin_view(finance_export_csv),   name="finance-export"),
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
    # ---------------------------
    # Attendance (JSON + Page)
    # ---------------------------
    path(
        "attendance/overview/<int:class_id>/",
        views.attendance_class_overview_json,
        name="attendance_class_overview_json",
    ),
    path(
        "attendance/day/<int:class_id>/",
        views.attendance_classday_get,
        name="attendance_classday_get",
    ),
    path(
        "attendance/day/upsert/",
        views.attendance_classday_upsert,
        name="attendance_classday_upsert",
    ),
    # PAGE VIEW (this is what templates should link to)
    path(
        "attendance/class/<int:class_id>/",
        ui_views.attendance_class_page,  # <-- use the page view, not the JSON view
        name="attendance_class_page",
    ),
    path("dj-admin/students/lookup/", admin.site.admin_view(student_lookup_admin), name="student-lookup"),
]


# Serve static & media in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
    if getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

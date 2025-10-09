# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import include, path

# Admin pages wrapped with admin_view
from content.admin import finance_overview_admin, student_ledger_admin
from content.views import (
    finance_export_csv,  # for /dj-admin/finance/export.csv
    build_student_lookup_context,
    my_invoices,  # student self-service
    invoice_pay, invoice_bulk_checkout_all, invoice_bulk_checkout_selected,
    invoice_bulk_checkout,  # student self-service -> pay one invoice
)

# Public UI views you already have
from ui import views as ui_views
from ui import views

# Honeypots / decoys
from accounts import views as acc_views


def student_lookup_admin(request):
    ctx = admin.site.each_context(request)
    ctx.update(build_student_lookup_context(request))
    ctx.setdefault("title", "Student Lookup")
    return TemplateResponse(request, "admin/students/lookup.html", ctx)


urlpatterns = [
    # ---------- Public site ----------
    path("", ui_views.home, name="home"),

    # Feature apps (namespaced)
    path("content/", include(("content.urls", "content"), namespace="content")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # ---------- Real Django admin (moved off /admin) ----------
    path("dj-admin/finance/overview/", admin.site.admin_view(finance_overview_admin), name="finance-overview"),
    path("dj-admin/finance/export.csv",  admin.site.admin_view(finance_export_csv),   name="finance-export"),
    path("dj-admin/finance/student-ledger/", admin.site.admin_view(student_ledger_admin), name="finance-student-ledger"),
    path("dj-admin/students/lookup/", admin.site.admin_view(student_lookup_admin), name="student-lookup"),
    path("dj-admin/", admin.site.urls),

    # ---------- Honeypot decoys at root ----------
    path("admin/", acc_views.honeypot, name="hp_admin_root"),
    path("admin/login/", acc_views.honeypot, name="hp_admin_login"),
    path("teacher/login/", acc_views.honeypot, name="hp_teacher_login"),
    path("teacher/signup/", acc_views.honeypot, name="hp_teacher_signup"),

    # ---------- Public pages you already use ----------
    path("notices/", ui_views.notices_list, name="notices_list"),
    path("notices/<int:pk>/", ui_views.notice_detail, name="notice_detail"),
    path("admissions/", include("content.urls_admissions", namespace="admissions")),
    path("contact/submit/", ui_views.contact_submit, name="contact_submit"),
    path("gallery/", views.gallery_page, name="gallery"),

    path("results/", views.results_index, name="index"),
    path("results/filter/", views.results_filter, name="results_filter"),
    path("results/<int:summary_id>/", views.results_detail, name="results_detail"),
    path("results-debug/", views.results_debug, name="results_debug"),

    # Attendance (page + JSON)
    path("attendance/overview/<int:class_id>/", views.attendance_class_overview_json, name="attendance_class_overview_json"),
    path("attendance/day/<int:class_id>/", views.attendance_classday_get, name="attendance_classday_get"),
    path("attendance/day/upsert/", views.attendance_classday_upsert, name="attendance_classday_upsert"),
    path("attendance/class/<int:class_id>/", ui_views.attendance_class_page, name="attendance_class_page"),

    # ---------- Student self-service (navbar) ----------
    path("me/invoices/", my_invoices, name="my-invoices"),
    path("me/invoices/<int:invoice_id>/pay/", invoice_pay, name="invoice-pay"),
    path("me/invoices/checkout/all/", invoice_bulk_checkout_all, name="invoice-bulk-checkout-all"),
    path("me/invoices/checkout/selected/", invoice_bulk_checkout_selected, name="invoice-bulk-checkout-selected"),
    path("me/invoices/checkout/", invoice_bulk_checkout, name="invoice-bulk-checkout"),
]

# Static/Media (dev only)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
    if getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

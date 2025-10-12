# content/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    # Public JSON for homepage
    api_slides, api_notices, api_timeline,

    # Manage (teacher/admin)
    manage_slide_create, manage_notice_create, manage_timeline_create,

    # Admissions flow
    AdmissionApplyView, AdmissionReviewView, AdmissionConfirmView, AdmissionReceiptView,

    # Payments (generic + PayPal + Stripe webhook & checkout)
    create_payment_order, mark_payment_paid,
    paypal_create, paypal_capture,
    stripe_webhook, stripe_checkout_create, stripe_checkout_success, stripe_checkout_cancel,

    # Finance overview + export + receipts
    finance_totals, finance_overview, finance_export_csv, receipt_by_txn,

    # Student invoices
    my_invoices, invoice_pay,
    invoice_bulk_checkout_all, invoice_bulk_checkout_selected, invoice_bulk_checkout, download_latest_receipt,
)

# These views live in ui.views but we expose them under the `content:` namespace
from ui.views import (
    exam_routines_page, exam_routine_detail, exam_routines_json,
    exam_routine_detail_json, exam_routine_detail_page,
    bus_routes_page, bus_route_detail_page, bus_routes_json, bus_route_detail_json,
    marksheet_search, marksheet_detail, marksheet_pdf,
)

app_name = "content"

# Secret manage prefix (optional)
P = getattr(settings, "SECRET_LOGIN_PREFIX", "x9f83").strip("/")

urlpatterns = [
    # ---------- Public read (homepage data) ----------
    path("api/slides/", api_slides, name="api_slides"),
    path("api/notices/", api_notices, name="api_notices"),
    path("api/timeline/", api_timeline, name="api_timeline"),

    # ---------- Admissions ----------
    path("apply/", AdmissionApplyView.as_view(), name="apply"),
    path("review/<int:pk>/", AdmissionReviewView.as_view(), name="review"),
    path("confirm/<int:pk>/", AdmissionConfirmView.as_view(), name="confirm"),
    path("receipt/<int:pk>/", AdmissionReceiptView.as_view(), name="receipt"),

    # Server-computed amount + admission mark-paid callback
    path("payment/<int:pk>/create/", create_payment_order, name="payment-create"),
    path("payment/<int:pk>/mark-paid/", mark_payment_paid, name="payment-mark-paid"),

    # ---------- PayPal helpers (dev) ----------
    path("pay/paypal/create/", paypal_create, name="paypal_create"),
    path("pay/paypal/capture/", paypal_capture, name="paypal_capture"),

    # ---------- Stripe checkout + webhook ----------
    path("pay/stripe/create/<int:invoice_id>/", stripe_checkout_create, name="stripe-checkout-create"),
    path("pay/stripe/success/", stripe_checkout_success, name="stripe-checkout-success"),
    path("pay/stripe/cancel/", stripe_checkout_cancel, name="stripe-checkout-cancel"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),

    # ---------- Manage (teacher/admin) behind secret prefix ----------
    path(f"{P}/manage/slides/create/", manage_slide_create, name="manage_slide_create"),
    path(f"{P}/manage/notices/create/", manage_notice_create, name="manage_notice_create"),
    path(f"{P}/manage/timeline/create/", manage_timeline_create, name="manage_timeline_create"),

    # ---------- Exam Corner (UI) ----------
    path("exam-routines/", exam_routines_page, name="exam_routines_page"),
    path("exam-routines/<int:pk>/", exam_routine_detail, name="exam_routine_detail"),
    path("api/exam-routines/", exam_routines_json, name="exam_routines_json"),
    path("api/exam-routines/<int:pk>/", exam_routine_detail_json, name="exam_routine_detail_json"),
    path("exams/routines/<int:pk>/", exam_routine_detail_page, name="exam_routine_detail_page"),

    # ---------- Bus routes (UI) ----------
    path("bus/", bus_routes_page, name="bus_routes_page"),
    path("bus/<int:pk>/", bus_route_detail_page, name="bus_route_detail_page"),
    path("bus/routes/", bus_routes_json, name="bus_routes_json"),
    path("bus/routes/<int:pk>/", bus_route_detail_json, name="bus_route_detail_json"),

    # ---------- Results / Marksheet ----------
    path("results/marksheets/", marksheet_search, name="marksheet_search"),
    path("results/marksheets/<int:pk>/", marksheet_detail, name="marksheet_detail"),
    path("results/marksheets/<int:pk>/pdf/", marksheet_pdf, name="marksheet_pdf"),

    # ---------- Finance (overview + CSV + receipt by txn) ----------
    path("api/finance/totals/", finance_totals, name="finance_totals"),
    path("admin/finance/overview/", finance_overview, name="finance-overview"),
    path("admin/finance/export/", finance_export_csv, name="finance-export"),
    path("admin/finance/receipt/txn/<str:txn_id>/", receipt_by_txn, name="receipt-by-txn"),

    # ---------- Student invoices (self-service) ----------
    path("me/invoices/", my_invoices, name="my-invoices"),
    path("me/invoices/<int:invoice_id>/pay/", invoice_pay, name="invoice-pay"),
    path("me/invoices/checkout/all/", invoice_bulk_checkout_all, name="invoice-bulk-checkout-all"),
    path("me/invoices/checkout/selected/", invoice_bulk_checkout_selected, name="invoice-bulk-checkout-selected"),
    path("me/invoices/checkout/", invoice_bulk_checkout, name="invoice-bulk-checkout"),
    path("receipts/<int:payment_id>/download/", download_latest_receipt, name="receipt-download"),
    path("checkout/selected/", invoice_bulk_checkout_selected, name="invoice-bulk-checkout-selected"),
]

# Media (dev)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

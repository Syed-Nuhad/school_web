from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from ui.views import (
    contact_submit, attendance_class_overview_json, exam_routine_detail_json,
    exam_routines_json, exam_routines_page, exam_routine_detail_page,
    exam_routine_detail, bus_routes_json, bus_route_detail_json,
    bus_route_detail_page, bus_routes_page, marksheet_pdf, marksheet_search,
    marksheet_detail
)

from .views import (
    api_slides, api_notices, api_timeline,
    manage_slide_create, manage_notice_create, manage_timeline_create,
    paypal_create, paypal_capture,
    AdmissionApplyView, AdmissionReviewView, AdmissionConfirmView, AdmissionReceiptView,
    create_payment_order, mark_payment_paid,
    finance_totals, finance_overview, finance_export_csv as finance_export,
)
# If you still need the alternative checkout flow from view_addmissions, import it,
# but avoid duplicating paths/names:
# from .view_addmissions import AdmissionCheckoutView, AdmissionSuccessView

app_name = "content"

P = getattr(settings, "SECRET_LOGIN_PREFIX", "x9f83").strip("/")

urlpatterns = [
    # Public read
    path("api/slides/", api_slides, name="api_slides"),
    path("api/notices/", api_notices, name="api_notices"),
    path("api/timeline/", api_timeline, name="api_timeline"),

    # Admissions core
    path("apply/", AdmissionApplyView.as_view(), name="apply"),
    path("review/<int:pk>/", AdmissionReviewView.as_view(), name="review"),
    path("confirm/<int:pk>/", AdmissionConfirmView.as_view(), name="confirm"),
    path("receipt/<int:pk>/", AdmissionReceiptView.as_view(), name="receipt"),

    # Payment (the pair from .views)
    path("payment/<int:pk>/create/", create_payment_order, name="payment-create"),
    path("payment/<int:pk>/mark-paid/", mark_payment_paid, name="payment-mark-paid"),

    # Optional: dev PayPal helpers
    path("pay/paypal/create/", paypal_create, name="paypal_create"),
    path("pay/paypal/capture/", paypal_capture, name="paypal_capture"),

    # Manage (behind secret prefix)
    path(f"{P}/manage/slides/create/", manage_slide_create, name="manage_slide_create"),
    path(f"{P}/manage/notices/create/", manage_notice_create, name="manage_notice_create"),
    path(f"{P}/manage/timeline/create/", manage_timeline_create, name="manage_timeline_create"),

    # Exam routines
    path("exam-routines/", exam_routines_page, name="exam_routines_page"),
    path("exam-routines/<int:pk>/", exam_routine_detail, name="exam_routine_detail"),
    path("api/exam-routines/", exam_routines_json, name="exam_routines_json"),
    path("api/exam-routines/<int:pk>/", exam_routine_detail_json, name="exam_routine_detail_json"),
    path("exams/routines/<int:pk>/", exam_routine_detail_page, name="exam_routine_detail_page"),

    # Bus routes
    path("bus/", bus_routes_page, name="bus_routes_page"),
    path("bus/<int:pk>/", bus_route_detail_page, name="bus_route_detail_page"),
    path("bus/routes/", bus_routes_json, name="bus_routes_json"),
    path("bus/routes/<int:pk>/", bus_route_detail_json, name="bus_route_detail_json"),

    # Results
    path("results/marksheets/", marksheet_search, name="marksheet_search"),
    path("results/marksheets/<int:pk>/", marksheet_detail, name="marksheet_detail"),
    path("results/marksheets/<int:pk>/pdf/", marksheet_pdf, name="marksheet_pdf"),

    # Finance
    path("api/finance/totals/", finance_totals, name="finance_totals"),
    path("admin/finance/overview/", finance_overview, name="finance-overview"),
    path("admin/finance/export/", finance_export, name="finance-export"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

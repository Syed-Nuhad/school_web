from django.conf import settings
from django.urls import path

from ui.views import contact_submit, attendance_class_overview_json
from . import views
from .view_addmissions import AdmissionApplyView, AdmissionSuccessView, AdmissionCheckoutView, payment_create, \
    payment_mark_paid
from .views import AdmissionReceiptView, AdmissionReviewView, AdmissionConfirmView, create_payment_order, \
    mark_payment_paid
from django.conf.urls.static import static


app_name = "content"

# secret prefix for “manage” endpoints
P = getattr(settings, "SECRET_LOGIN_PREFIX", "x9f83").strip("/")

urlpatterns = [
    # public read (homepage)
    path("api/slides/", views.api_slides, name="api_slides"),
    path("api/notices/", views.api_notices, name="api_notices"),
    path("api/timeline/", views.api_timeline, name="api_timeline"),
    path("apply/", AdmissionApplyView.as_view(), name="apply"),
    path("apply/success/", AdmissionSuccessView.as_view(), name="success"),
    # teacher/admin create
    path(f"{P}/manage/slides/create/", views.manage_slide_create, name="manage_slide_create"),
    path(f"{P}/manage/notices/create/", views.manage_notice_create, name="manage_notice_create"),
    path(f"{P}/manage/timeline/create/", views.manage_timeline_create, name="manage_timeline_create"),

    # PayPal
    path("pay/paypal/create/", views.paypal_create, name="paypal_create"),
    path("pay/paypal/capture/", views.paypal_capture, name="paypal_capture"),

    path("apply/", AdmissionApplyView.as_view(), name="apply"),
    path("review/<int:pk>/", AdmissionReviewView.as_view(), name="review"),
    path("confirm/<int:pk>/", AdmissionConfirmView.as_view(), name="confirm"),
    path("receipt/<int:pk>/", AdmissionReceiptView.as_view(), name="receipt"),
    path("review/<int:pk>/", AdmissionReviewView.as_view(), name="review"),

    # payment API
    path("payment/<int:pk>/create/", create_payment_order, name="payment-create"),
    path("payment/<int:pk>/mark-paid/", mark_payment_paid, name="payment-mark-paid"),
    path("checkout/<int:pk>/", AdmissionCheckoutView.as_view(), name="checkout"),
    path("success/", AdmissionSuccessView.as_view(), name="success"),

    # payment endpoints used by your checkout JS
    path("<int:pk>/payment/create/", payment_create, name="payment-create"),
    path("<int:pk>/payment/mark-paid/", payment_mark_paid, name="payment-mark-paid"),
    path("contact/submit/", contact_submit, name="contact_submit"),
    # ... your existing urls ...
    path("attendance/overview/<int:class_id>/", attendance_class_overview_json,
         name="attendance_class_overview_json"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
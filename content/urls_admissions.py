# content/urls_admissions.py
from django.urls import path

from content.view_addmissions import AdmissionApplyView, AdmissionSuccessView, AdmissionCheckoutView, PaymentCreateAPI, \
    PaymentMarkPaidAPI, payment_mark_paid, payment_create

app_name = "admissions"

urlpatterns = [
    path("apply/", AdmissionApplyView.as_view(), name="apply"),
    path("apply/success/", AdmissionSuccessView.as_view(), name="success"),
    path("<int:pk>/checkout/", AdmissionCheckoutView.as_view(), name="checkout"),

    # JSON endpoints used by checkout page
    path("<int:pk>/pay/create/", payment_create, name="payment-create"),
    path("<int:pk>/pay/mark-paid/", payment_mark_paid, name="payment-mark-paid"),
]

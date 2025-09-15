from django.conf import settings
from django.urls import path
from . import views
from . import views
from .view_addmissions import AdmissionApplyView, AdmissionSuccessView

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

    path("pay/bkash/init/", views.bkash_init, name="bkash_init"),
    path("pay/bkash/return/", views.bkash_return, name="bkash_return"),

    # PayPal
    path("pay/paypal/create/", views.paypal_create, name="paypal_create"),
    path("pay/paypal/capture/", views.paypal_capture, name="paypal_capture"),
]

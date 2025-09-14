# content/urls_admissions.py
from django.urls import path

from content.view_addmissions import AdmissionApplyView, AdmissionSuccessView

app_name = "admissions"

urlpatterns = [
    path("apply/", AdmissionApplyView.as_view(), name="apply"),
    path("apply/success/", AdmissionSuccessView.as_view(), name="success"),
]

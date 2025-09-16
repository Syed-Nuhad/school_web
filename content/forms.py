# content/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator

from .models import AdmissionApplication

PHONE_RE = RegexValidator(
    regex=r"^01\d{9}$",
    message="Enter a valid BD mobile number (11 digits, starts with 01)."
)


class AdmissionApplicationForm(forms.ModelForm):
    """
    IMPORTANT: include the three add-on booleans in Meta.fields
    so the POSTed checkboxes bind to the model and reach form_valid().
    """
    add_bus       = forms.BooleanField(required=False, label="Add School Bus")
    add_hostel    = forms.BooleanField(required=False, label="Add Hostel Seat")
    add_marksheet = forms.BooleanField(required=False, label="Add Exact Marksheet")  # <-- make sure this exists

    class Meta:
        model = AdmissionApplication
        fields = [
            "full_name","email","phone","date_of_birth","address",
            "guardian_name","guardian_phone","desired_course","shift",
            "previous_school","ssc_gpa","photo","transcript","message",
            "add_bus","add_hostel","add_marksheet",  # <-- included
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "01XXXXXXXXX"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),

            "desired_course": forms.Select(attrs={"class": "form-select"}),
            "shift": forms.TextInput(attrs={"class": "form-control"}),
            "previous_school": forms.TextInput(attrs={"class": "form-control"}),
            "ssc_gpa": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "5"}),

            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "transcript": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),

            # render as checkboxes
            "add_bus": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "optBus"}),
            "add_hostel": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "optHostel"}),
            "add_marksheet": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "optMarksheet"}),
        }

        labels = {
            "add_bus": "Add School Bus",
            "add_hostel": "Add Hostel Seat",
            "add_marksheet": "Add Exact Marksheet",
        }

    # --- OPTIONAL light validation / normalization ---

    def clean_phone(self):
        p = (self.cleaned_data.get("phone") or "").strip()
        if p and not p.isdigit():
            raise ValidationError("Phone must be numeric (digits only).")
        if p and not (p.startswith("01") and 10 <= len(p) <= 11):
            # allow 10/11 depending on your rule; adjust if needed
            raise ValidationError("Phone must start with 01 and be 10–11 digits.")
        return p

    def clean_guardian_phone(self):
        gp = (self.cleaned_data.get("guardian_phone") or "").strip()
        if gp and not gp.isdigit():
            raise ValidationError("Guardian phone must be numeric (digits only).")
        return gp

    def clean_ssc_gpa(self):
        gpa = self.cleaned_data.get("ssc_gpa")
        if gpa is not None and (gpa < 0 or gpa > 5):
            raise ValidationError("GPA must be between 0.00 and 5.00.")
        return gpa
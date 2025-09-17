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
    ModelForm for the admission application.

    Notes:
    - The template renders the FIRST THREE checkboxes manually:
        add_admission, add_tuition, add_exam
      but we still include them in Meta.fields so POST values bind to the form/model.
    - The other three (add_bus, add_hostel, add_marksheet) are rendered with {{ form.* }}.
    """
    class Meta:
        model = AdmissionApplication
        fields = [
            "full_name", "email", "phone", "date_of_birth", "address",
            "guardian_name", "guardian_phone", "desired_course", "shift",
            "previous_school", "ssc_gpa", "photo", "transcript", "message",
            # all six selections must be in fields to bind POSTed values
            "add_admission", "add_tuition", "add_exam",
            "add_bus", "add_hostel", "add_marksheet",
        ]
        widgets = {
            "full_name":      forms.TextInput(attrs={"class": "form-control"}),
            "email":          forms.EmailInput(attrs={"class": "form-control"}),
            "phone":          forms.TextInput(attrs={"class": "form-control", "placeholder": "01XXXXXXXXX"}),
            "date_of_birth":  forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "address":        forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "guardian_name":  forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "desired_course": forms.Select(attrs={"class": "form-select"}),
            "shift":          forms.TextInput(attrs={"class": "form-control"}),
            "previous_school":forms.TextInput(attrs={"class": "form-control"}),
            "ssc_gpa":        forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "5"}),
            "photo":          forms.ClearableFileInput(attrs={"class": "form-control"}),
            "transcript":     forms.ClearableFileInput(attrs={"class": "form-control"}),
            "message":        forms.Textarea(attrs={"class": "form-control", "rows": 3}),

            # These three are rendered by {{ form.* }} in your table (left-side checkbox).
            "add_bus":        forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "add_hostel":     forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "add_marksheet":  forms.CheckboxInput(attrs={"class": "form-check-input"}),

            # These three are rendered manually in the template (ids already set there),
            # but keeping widgets is harmless and ensures binding if you ever render them via {{ form.* }}.
            "add_admission":  forms.CheckboxInput(attrs={"class": "form-check-input", "id": "add_admission"}),
            "add_tuition":    forms.CheckboxInput(attrs={"class": "form-check-input", "id": "add_tuition"}),
            "add_exam":       forms.CheckboxInput(attrs={"class": "form-check-input", "id": "add_exam"}),
        }
        labels = {
            "add_bus": "Add School Bus",
            "add_hostel": "Add Hostel Seat",
            "add_marksheet": "Add Exact Marksheet",
        }

    # --- Validation ---
    def clean_phone(self):
        p = (self.cleaned_data.get("phone") or "").strip()
        if p:
            PHONE_RE(p)  # raises ValidationError if not matched
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
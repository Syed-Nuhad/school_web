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
    # explicit add-on checkboxes (tie to model booleans)
    add_bus = forms.BooleanField(required=False)
    add_hostel = forms.BooleanField(required=False)
    add_marksheet = forms.BooleanField(required=False)

    class Meta:
        model = AdmissionApplication
        fields = [
            "full_name", "email", "phone", "date_of_birth", "address",
            "guardian_name", "guardian_phone",
            "desired_course", "shift",
            "previous_school", "ssc_gpa",
            "photo", "transcript",
            "message",
            "add_bus", "add_hostel", "add_marksheet",
        ]

        # Minimal attrs; Bootstrap classes can be added in __init__
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

        help_texts = {
            "transcript": "PDF/JPG/PNG up to 10 MB.",
            "photo": "JPG/PNG up to 5 MB.",
        }

    phone = forms.CharField(validators=[PHONE_RE])
    guardian_phone = forms.CharField(validators=[PHONE_RE], required=False)

    transcript = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])]
    )
    photo = forms.ImageField(required=False)

    MAX_TRANSCRIPT_MB = 10
    MAX_PHOTO_MB = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # add Bootstrap classes conservatively (keeps template clean)
        for name, field in self.fields.items():
            if hasattr(field.widget, "input_type") and field.widget.input_type in ("file", "select"):
                # select/file -> form-select or form-control (file is also fine w/ form-control in BS5)
                if field.widget.input_type == "select":
                    field.widget.attrs.setdefault("class", "form-select")
                else:
                    field.widget.attrs.setdefault("class", "form-control")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_transcript(self):
        f = self.cleaned_data.get("transcript")
        if f and f.size > self.MAX_TRANSCRIPT_MB * 1024 * 1024:
            raise ValidationError(f"Transcript too large (>{self.MAX_TRANSCRIPT_MB} MB).")
        return f

    def clean_photo(self):
        f = self.cleaned_data.get("photo")
        if f and f.size > self.MAX_PHOTO_MB * 1024 * 1024:
            raise ValidationError(f"Photo too large (>{self.MAX_PHOTO_MB} MB).")
        return f
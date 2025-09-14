# content/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator

from .models import AdmissionApplication

PHONE_RE = RegexValidator(
    regex=r"^[0-9+\-\s()]{7,}$",
    message="Enter a valid phone number.",
)

class AdmissionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdmissionApplication
        fields = [
            "full_name", "email", "phone", "date_of_birth", "address",
            "guardian_name", "guardian_phone",
            "desired_course", "shift",
            "previous_school", "ssc_gpa",
            "photo", "transcript",
            "message",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "desired_course": "Choose the course you want to apply for.",
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

# accounts/forms.py
from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, HTML, Column, Row, Layout
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from content.models import AcademicClass, StudentProfile  # uses your existing models



User = get_user_model()


class BaseSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap classes + placeholders
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "choose a username",
            "autocomplete": "username",
        })
        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "you@example.com",
            "autocomplete": "email",
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "create a password",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "repeat password",
            "autocomplete": "new-password",
        })


class StudentSignupForm(BaseSignupForm):
    """Use in /accounts/signup/student/"""
    pass


class StaffSignupForm(BaseSignupForm):
    """Use for teacher/admin secret signup views; set role in the view."""
    pass


class PublicLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "your username",
            "autocomplete": "username",
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "your password",
            "autocomplete": "current-password",
        })


class SlimAuthForm(AuthenticationForm):
    """Alternative minimal login form with Bootstrap class on all fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")




class StudentRegisterForm(forms.Form):
    full_name    = forms.CharField(max_length=150, label="Full name")
    username     = forms.CharField(max_length=150, label="Username")
    email        = forms.EmailField(required=False, label="Email")
    password1    = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2    = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    school_class = forms.ModelChoiceField(
        queryset=AcademicClass.objects.all().order_by("-year", "name"),
        label="Class"
    )
    section      = forms.CharField(max_length=5, label="Section")
    roll_number  = forms.IntegerField(min_value=1, label="Roll number")

    def clean_username(self):
        u = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=u).exists():
            raise ValidationError("That username is already taken.")
        return u

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get("password1")
        pwd2 = cleaned.get("password2")
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error("password2", "Passwords do not match.")

        klass  = cleaned.get("school_class")
        sect   = (cleaned.get("section") or "").strip()
        roll   = cleaned.get("roll_number")

        if not klass or not sect or not roll:
            return cleaned  # field-level errors will show

        # normalize section
        sect_norm = sect.upper()
        cleaned["section"] = sect_norm

        # Try to find an existing profile for that Class/Section/Roll
        sp = StudentProfile.objects.filter(
            school_class=klass, section__iexact=sect_norm, roll_number=roll
        ).first()

        if sp:
            if sp.user_id:
                # Same student seat already has an account
                raise ValidationError("This Class/Section/Roll is already linked to another account.")
            # OK: existing unlinked profile → link it
            cleaned["_student_profile"] = sp
            cleaned["_create_profile"] = False
        else:
            # No profile exists. Allow creation if the flag is on; otherwise error.
            if getattr(settings, "ALLOW_STUDENT_PROFILE_CREATE_ON_SIGNUP", False):
                cleaned["_student_profile"] = None
                cleaned["_create_profile"] = True
            else:
                raise ValidationError(
                    "No student record found for that Class/Section/Roll. Please contact the office."
                )

        return cleaned
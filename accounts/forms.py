# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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

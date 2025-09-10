# accounts/urls.py
from django.conf import settings
from django.urls import path
from . import views

app_name = "accounts"

LOGIN_PREFIX = getattr(settings, "SECRET_LOGIN_PREFIX", "x9f83").strip("/")
SIGNUP_PREFIX = getattr(settings, "SECRET_SIGNUP_PREFIX", "k7p1a").strip("/")


P = getattr(settings, "SECRET_LOGIN_PREFIX", "x9f83").strip("/")
S = getattr(settings, "SECRET_SIGNUP_PREFIX", "k7p1a").strip("/")


urlpatterns = [
    # ---- Public (students) ----
    # Give the student login the name "login_public" so your template link works.
    path("login/", views.login_student, name="login_public"),
    # Optional second path that points to the same view (keep if you like this URL too)
    path("login/student/", views.login_student, name="login_student"),

    path("signup/student/", views.signup_student, name="signup_student"),
    path("logout/", views.logout_view, name="logout"),

    # ---- Secret teacher endpoints ----
    path(f"{LOGIN_PREFIX}/login/teacher/", views.login_teacher, name="login_teacher"),
    path(f"{SIGNUP_PREFIX}/signup/teacher/", views.signup_teacher, name="signup_teacher"),

    # ---- Secret admin endpoints ----
    path(f"{LOGIN_PREFIX}/login/admin/", views.login_admin, name="login_admin"),
    path(f"{SIGNUP_PREFIX}/signup/admin/", views.signup_admin, name="signup_admin"),

    # 2FA verify endpoint (secret prefix)
    path(f"{P}/verify/", views.verify_code, name="verify_code"),
    path(f"{P}verify/", views.verify_code, name="verify_code"),
    path(f"{P}verify/resend/", views.resend_code, name="resend_code"),
]

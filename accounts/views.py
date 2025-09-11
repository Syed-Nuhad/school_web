# accounts/views.py
# =============================================================================
# (1) IMPORTS
# =============================================================================
from __future__ import annotations

import random
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import StudentSignupForm, StaffSignupForm, SlimAuthForm
from .models import SecurityLog

User = get_user_model()


# =============================================================================
# (2) ROLE CONSTANTS  (string-based so it works with or without a User.role field)
# =============================================================================
ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"
ROLE_ADMIN   = "admin"


# =============================================================================
# (3) 2FA SESSION KEYS & LIMITS  (single source of truth for 2FA)
# =============================================================================
SESSION_2FA_UID       = "2fa_uid"        # user pk awaiting verification
SESSION_2FA_EMAIL     = "2fa_email"      # email we sent code to
SESSION_2FA_CODE      = "2fa_code"       # 6-digit code
SESSION_2FA_EXPIRES   = "2fa_expires"    # ISO string of expiry
SESSION_2FA_RESENDS   = "2fa_resends"    # number of resends used
SESSION_2FA_LAST_SEND = "2fa_last_send"  # ISO string of last send time

CODE_TTL_MINUTES          = 5   # code expiry
RESEND_COOLDOWN_SECONDS   = 30  # wait between resends
RESEND_MAX                = 3   # max resends allowed


# =============================================================================
# (4) SMALL HELPERS
# =============================================================================
def _now():
    """Return an aware 'now'."""
    return timezone.now()

def _from_iso(s: str) -> datetime:
    """
    Parse ISO string to aware datetime. (Django stores tz-aware now().isoformat()).
    If tz-naive gets in, make it aware in current timezone.
    """
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)
    return dt

def _client_ip(request):
    """Best-effort client IP extraction."""
    hdr = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return hdr.split(",")[0].strip() if hdr else request.META.get("REMOTE_ADDR")

def too_many_requests(request, exception=None):
    """Basic 429 view (if you ever plug it to throttling)."""
    return HttpResponse("Too many attempts. Please try again later.", status=429)

def honeypot(request):
    """
    (Security) Log and 404 any decoy endpoints such as /admin or fake teacher/admin login.
    """
    SecurityLog.objects.create(
        ip=_client_ip(request),
        path=request.path,
        action="HONEYPOT_HIT",
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        meta={"method": request.method},
    )
    return HttpResponseNotFound("Not found")

def _ensure_groups():
    """Make sure our 3 groups exist (idempotent)."""
    for name in ["Admin", "Teacher", "Student"]:
        Group.objects.get_or_create(name=name)


def _assign_role_or_group(user: User, role: str):
    """
    Give the user a role (if your model has a `role` field),
    put them in the matching Django group, and
    mark teachers/admins as staff so they can log into /dj-admin/.
    """
    # 1) Save role if your User has a 'role' field
    if hasattr(user, "role"):
        user.role = role

    # 2) Allow admin-site access for teachers/admins
    if role in (ROLE_TEACHER, ROLE_ADMIN):
        user.is_staff = True     # <--- THIS lets them access /dj-admin/

    # Optional: if you want true superuser for admins, uncomment:
    # if role == ROLE_ADMIN:
    #     user.is_superuser = True

    user.save()  # single save is fine

    # 3) Ensure group exists and add the user to it
    _ensure_groups()
    from django.contrib.auth.models import Group
    if role == ROLE_ADMIN:
        grp = Group.objects.get(name="Admin")
    elif role == ROLE_TEACHER:
        grp = Group.objects.get(name="Teacher")
    else:
        grp = Group.objects.get(name="Student")
    user.groups.add(grp)

def _user_has_role(user: User, role: str) -> bool:
    """
    (6) Check if user matches expected role.
        Priority: role field -> groups fallback.
    """
    if hasattr(user, "role"):
        return getattr(user, "role", None) == role

    # fallback via groups
    mapping = {"Admin": ROLE_ADMIN, "Teacher": ROLE_TEACHER, "Student": ROLE_STUDENT}
    return any(mapping.get(g.name) == role for g in user.groups.all())

def _redirect_after_login(user: User):
    """
    (7) Centralize post-login redirect. Customize per role when you have dashboards.
    """
    # if _user_has_role(user, ROLE_ADMIN): return redirect("admin_dashboard")
    # if _user_has_role(user, ROLE_TEACHER): return redirect("teacher_dashboard")
    return redirect("home")


# =============================================================================
# (8) 2FA CORE (with RESEND support)
# =============================================================================
def _issue_new_code() -> str:
    """Six-digit numeric code as string."""
    return f"{random.randint(0, 999_999):06d}"

def _send_code_email(to_email: str, code: str):
    """
    Email the verification code using your configured EMAIL_BACKEND.
    """
    if not to_email:
        return
    subject = "Your verification code"
    body = (
        f"Your login verification code is: {code}\n"
        f"This code expires in {CODE_TTL_MINUTES} minutes."
    )
    send_mail(
        subject,
        body,
        getattr(settings, "DEFAULT_FROM_EMAIL", None),
        [to_email],
        fail_silently=False,  # raise in dev to see errors; switch to True if desired
    )

def _start_2fa(request, user: User, role_label: str):
    """
    (8.1) Begin a 2FA session for 'user' logging in via 'role_label' portal.
          Generates code, stores session, emails code, and redirects to verify page.
    """
    code = _issue_new_code()
    request.session[SESSION_2FA_UID] = user.pk
    request.session[SESSION_2FA_EMAIL] = (user.email or "").strip()
    request.session[SESSION_2FA_CODE] = code
    request.session[SESSION_2FA_EXPIRES] = (_now() + timedelta(minutes=CODE_TTL_MINUTES)).isoformat()
    request.session[SESSION_2FA_RESENDS] = 0
    request.session[SESSION_2FA_LAST_SEND] = _now().isoformat()

    to_email = request.session[SESSION_2FA_EMAIL]
    if to_email:
        _send_code_email(to_email, code)
        messages.info(request, f"We sent a code to {to_email}.")
    else:
        messages.warning(request, "No email is set on your account; cannot send code.")

    # Optional debug hint:
    if settings.DEBUG:
        messages.info(request, f"[DEBUG] Code: {code}")

    return redirect("accounts:verify_code")


def verify_code(request):
    """
    (8.2) Show the 2FA input form & validate code.
          On success => log in the stored user and clear 2FA session keys.
    """
    uid = request.session.get(SESSION_2FA_UID)
    email = request.session.get(SESSION_2FA_EMAIL, "")
    code_expected = request.session.get(SESSION_2FA_CODE)
    expires_iso = request.session.get(SESSION_2FA_EXPIRES)
    resends_used = int(request.session.get(SESSION_2FA_RESENDS, 0))

    if not (uid and code_expected and expires_iso):
        messages.error(request, "Your verification session expired. Please log in again.")
        return redirect("accounts:login_student")

    expires = _from_iso(expires_iso)
    seconds_remaining = max(0, int((expires - _now()).total_seconds()))

    if request.method == "POST":
        submitted = (request.POST.get("code") or "").strip()

        if seconds_remaining <= 0:
            messages.error(request, "Code expired. Please resend a new code.")
            return redirect("accounts:verify_code")

        if submitted != code_expected:
            messages.error(request, "Incorrect code. Try again or resend.")
            return redirect("accounts:verify_code")

        # Success: log in the user and clear 2FA session keys.
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            messages.error(request, "User not found. Please log in again.")
            return redirect("accounts:login_student")

        for k in (
            SESSION_2FA_UID, SESSION_2FA_EMAIL, SESSION_2FA_CODE, SESSION_2FA_EXPIRES,
            SESSION_2FA_RESENDS, SESSION_2FA_LAST_SEND
        ):
            request.session.pop(k, None)

        login(request, user)
        messages.success(request, "Verification successful. You’re now signed in.")
        return _redirect_after_login(user)

    # GET -> render entry form
    ctx = {
        "email": email,
        "seconds_remaining": seconds_remaining,
        "resends_left": max(0, RESEND_MAX - resends_used),
    }
    return render(request, "accounts/verify_code.html", ctx)


def resend_code(request):
    """
    (8.3) Allow re-sending the 2FA code with cooldown and max attempts.
          POST only. Redirect back to verify page.
    """
    if request.method != "POST":
        return redirect("accounts:verify_code")

    uid = request.session.get(SESSION_2FA_UID)
    email = request.session.get(SESSION_2FA_EMAIL, "")
    if not (uid and email):
        messages.error(request, "Your verification session expired. Please log in again.")
        return redirect("accounts:login_student")

    # Throttle
    resends = int(request.session.get(SESSION_2FA_RESENDS, 0))
    if resends >= RESEND_MAX:
        messages.error(request, "Resend limit reached. Please start again.")
        return redirect("accounts:verify_code")

    last_send_iso = request.session.get(SESSION_2FA_LAST_SEND)
    if last_send_iso:
        last_send = _from_iso(last_send_iso)
        elapsed = (_now() - last_send).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
            messages.warning(request, f"Please wait {wait}s before requesting another code.")
            return redirect("accounts:verify_code")

    # Issue new code + extend expiry
    new_code = _issue_new_code()
    request.session[SESSION_2FA_CODE] = new_code
    request.session[SESSION_2FA_EXPIRES] = (_now() + timedelta(minutes=CODE_TTL_MINUTES)).isoformat()
    request.session[SESSION_2FA_RESENDS] = resends + 1
    request.session[SESSION_2FA_LAST_SEND] = _now().isoformat()

    _send_code_email(email, new_code)
    if settings.DEBUG:
        messages.info(request, f"[DEBUG] New code: {new_code}")

    messages.success(request, f"A new code was sent to {email}.")
    return redirect("accounts:verify_code")


# =============================================================================
# (9) PUBLIC: STUDENT AUTH (no 2FA)
# =============================================================================
def login_student(request):
    """
    Student login (no 2FA). If a teacher/admin tries here, nudge them to use
    the correct portal to avoid bypassing controls & routing.
    """
    form = SlimAuthForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if _user_has_role(user, ROLE_TEACHER) or _user_has_role(user, ROLE_ADMIN):
            messages.error(request, "Use the staff portal for your role.")
            return render(request, "accounts/login.html", {"form": form, "role": ROLE_STUDENT})
        login(request, user)
        return _redirect_after_login(user)

    return render(request, "accounts/login.html", {"form": form, "role": ROLE_STUDENT})


def signup_student(request):
    """
    Minimal student self-signup. Assign Student group/role after creation.
    """
    form = StudentSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        _assign_role_or_group(user, ROLE_STUDENT)
        messages.success(request, "Student account created. Please log in.")
        return redirect("accounts:login_student")

    return render(request, "accounts/signup.html", {"form": form, "role": ROLE_STUDENT})


# =============================================================================
# (10) SECRET: TEACHER / ADMIN AUTH (password + email 2FA)
# =============================================================================
def login_teacher(request):
    """Teacher password login that triggers email 2FA."""
    return _generic_login(request, role=ROLE_TEACHER, require_2fa=True)

def login_admin(request):
    """Admin password login that triggers email 2FA."""
    return _generic_login(request, role=ROLE_ADMIN, require_2fa=True)

def _generic_login(request, role: str, require_2fa: bool = False):
    """
    Shared staff login UI:
      - Confirms the account belongs to the portal's role.
      - If require_2fa=True, sends code and redirects to verify.
    """
    form = SlimAuthForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()

        if not _user_has_role(user, role):
            messages.error(request, "This account doesn’t match this portal.")
            SecurityLog.objects.create(
                ip=_client_ip(request),
                path=request.path,
                action="WRONG_PORTAL_ROLE",
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                meta={"expected": role, "user_id": user.pk},
            )
            return render(request, "accounts/login.html", {"form": form, "role": role})

        if require_2fa:
            return _start_2fa(request, user, role)

        login(request, user)
        return _redirect_after_login(user)

    return render(request, "accounts/login.html", {"form": form, "role": role})


# =============================================================================
# (11) SECRET: STAFF SIGNUP (invite token required)
# =============================================================================
def signup_teacher(request):
    """Token-protected teacher signup."""
    token = getattr(settings, "TEACHER_SIGNUP_TOKEN", "")
    return _protected_staff_signup(request, desired_role=ROLE_TEACHER, token=token)

def signup_admin(request):
    """Token-protected admin signup."""
    token = getattr(settings, "ADMIN_SIGNUP_TOKEN", "")
    return _protected_staff_signup(request, desired_role=ROLE_ADMIN, token=token)

def _protected_staff_signup(request, desired_role: str, token: str):
    """
    Staff self-creation behind a secret invite token.
    """
    form = StaffSignupForm(request.POST or None)

    if request.method == "POST":
        provided = (request.POST.get("invite_token") or "").strip()

        if not token or provided != token:
            SecurityLog.objects.create(
                ip=_client_ip(request),
                path=request.path,
                action="INVALID_INVITE_TOKEN",
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                meta={"provided": bool(provided), "desired_role": desired_role},
            )
            return HttpResponseForbidden("Invalid token.")

        if form.is_valid():
            user = form.save()
            _assign_role_or_group(user, desired_role)
            messages.success(request, "Staff account created.")
            return redirect("accounts:login_admin" if desired_role == ROLE_ADMIN else "accounts:login_teacher")

    return render(request, "accounts/staff_signup.html", {"form": form, "role": desired_role})


# =============================================================================
# (12) LOGOUT
# =============================================================================
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login_student")

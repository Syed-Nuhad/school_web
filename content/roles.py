# content/roles.py
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def is_teacher(user):
    if not user.is_authenticated:
        return False
    if getattr(user, "role", None) == "teacher":
        return True
    return user.groups.filter(name="Teacher").exists()

def is_admin(user):
    if not user.is_authenticated:
        return False
    if getattr(user, "role", None) == "admin":
        return True
    return user.is_staff or user.is_superuser or user.groups.filter(name="Admin").exists()

def is_teacher_or_admin(user):
    return is_teacher(user) or is_admin(user)

def teacher_or_admin_required(view):
    @login_required
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not is_teacher_or_admin(request.user):
            return HttpResponseForbidden("Not allowed.")
        return view(request, *args, **kwargs)
    return _wrapped

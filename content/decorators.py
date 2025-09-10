from functools import wraps
from django.http import HttpResponseForbidden
from .roles import is_admin, is_teacher

def teacher_or_admin_required(viewfunc):
    @wraps(viewfunc)
    def _wrapped(request, *args, **kwargs):
        if is_teacher(request.user) or is_admin(request.user):
            return viewfunc(request, *args, **kwargs)
        return HttpResponseForbidden("Not allowed.")
    return _wrapped

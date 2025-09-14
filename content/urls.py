from django.conf import settings
from django.urls import path
from . import views
from . import views

app_name = "content"

# secret prefix for “manage” endpoints
P = getattr(settings, "SECRET_LOGIN_PREFIX", "x9f83").strip("/")

urlpatterns = [
    # public read (homepage)
    path("api/slides/", views.api_slides, name="api_slides"),
    path("api/notices/", views.api_notices, name="api_notices"),
    path("api/timeline/", views.api_timeline, name="api_timeline"),

    # teacher/admin create
    path(f"{P}/manage/slides/create/", views.manage_slide_create, name="manage_slide_create"),
    path(f"{P}/manage/notices/create/", views.manage_notice_create, name="manage_notice_create"),
    path(f"{P}/manage/timeline/create/", views.manage_timeline_create, name="manage_timeline_create"),
]

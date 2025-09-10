from django.contrib import admin
from .models import Banner, Notice, TimelineEvent


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "is_active", "created_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    ordering = ("order", "-created_at")

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "grade", "section", "is_active", "posted_by", "published_at")
    list_filter = ("is_active", "grade", "section")
    search_fields = ("title", "body")
    date_hierarchy = "published_at"


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "date", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "description")
    list_filter = ("is_active", "date")
    autocomplete_fields = ("created_by",)

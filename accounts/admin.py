from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# Register your models here.
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_active", "last_login")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role & Preferences", {"fields": ("role", "pref_language", "pref_theme")}),
    )
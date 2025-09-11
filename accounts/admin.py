from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    # Optional: if your custom User has extra fields like `role`, add them:
    # If you DON'T have a `role` field, delete this `fieldsets +=` block.
    fieldsets = BaseUserAdmin.fieldsets + (
        ("App Fields", {"fields": ("role",)}),
    )

    # Optional display tweaks
    list_display = ("username", "email", "is_staff", "is_active")
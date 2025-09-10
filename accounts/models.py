from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)

    # Preferences we’ll use later for i18n/theme (safe to add now)
    pref_language = models.CharField(max_length=8, default="en")
    pref_theme = models.CharField(max_length=8, default="light")

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self): return self.role == self.Role.ADMIN
    @property
    def is_teacher(self): return self.role == self.Role.TEACHER
    @property
    def is_student(self): return self.role == self.Role.STUDENT


class SecurityLog(models.Model):
    ACTION_CHOICES = [
        ("HONEYPOT_HIT", "Honeypot hit"),
        ("FAILED_LOGIN", "Failed login"),
        ("BLOCKED", "Blocked"),
        ("RATE_LIMIT", "Rate limited"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=512)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    user_agent = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)   # <- dict default!

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["ip", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.ip} {self.path} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
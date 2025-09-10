from django import forms
from .models import Banner, Notice


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["title", "subtitle", "image", "image_url",
                  "button_text", "button_link", "order", "is_active"]

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["title", "body", "image", "image_url",
                  "grade", "section", "link_url",
                  "is_active", "published_at"]
        widgets = {
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
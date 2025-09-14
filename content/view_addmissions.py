from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, FormView

from .models import AdmissionApplication, Course
from .forms import AdmissionApplicationForm



class AdmissionApplyView(FormView):
    template_name = "admissions/apply.html"   # frontend later
    form_class = AdmissionApplicationForm
    success_url = reverse_lazy("admissions:success")

    def get_initial(self):
        initial = super().get_initial()
        course_id = self.request.GET.get("course")
        if course_id:
            initial["desired_course"] = course_id
        if self.request.user.is_authenticated:
            initial.setdefault("email", getattr(self.request.user, "email", ""))
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        # If course passed in querystring, trust it over form (optional)
        course_id = self.request.GET.get("course")
        if course_id:
            obj.desired_course = Course.objects.filter(pk=course_id).first() or obj.desired_course
        if self.request.user.is_authenticated:
            obj.created_by = self.request.user
        obj.save()
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cid = self.request.GET.get("course")
        ctx["selected_course"] = Course.objects.filter(pk=cid).first()
        return ctx

class AdmissionSuccessView(TemplateView):
    template_name = "admissions/success.html"  # frontend later
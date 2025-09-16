from decimal import Decimal

from django.shortcuts import redirect
from django.views.generic import TemplateView, CreateView

from content.forms import AdmissionApplicationForm
from content.models import Course, AdmissionApplication





class AdmissionSuccessView(TemplateView):
    template_name = "admissions/success.html"
class AdmissionApplyView(CreateView):
    model = AdmissionApplication
    form_class = AdmissionApplicationForm
    template_name = "admissions/apply.html"

    def get_initial(self):
        initial = super().get_initial()
        course_id = self.request.GET.get("course")
        if course_id:
            try:
                initial["desired_course"] = Course.objects.get(pk=course_id)
            except Course.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = None

        # try from GET preselect
        cid = self.request.GET.get("course")
        if cid:
            course = Course.objects.filter(pk=cid).first()

        # or from form (re-renders on invalid POST)
        form = ctx.get("form")
        if not course and form:
            course = form.initial.get("desired_course") or getattr(form.instance, "desired_course", None)

        ctx["selected_course"] = course
        if course:
            fa = course.admission_fee or Decimal("0")
            ft = course.first_month_tuition or Decimal("0")
            fe = course.exam_fee or Decimal("0")
            ctx["fee_admission"] = fa
            ctx["fee_tuition"]   = ft
            ctx["fee_exam"]      = fe
            ctx["fee_total"]     = fa + ft + fe  # base subtotal for display only
        return ctx

    def form_valid(self, form):
        app = form.save(commit=False)
        course = app.desired_course

        # snapshot prices from course
        app.fee_admission = course.admission_fee or Decimal("0")
        app.fee_tuition   = course.first_month_tuition or Decimal("0")
        app.fee_exam      = course.exam_fee or Decimal("0")
        app.fee_bus       = course.bus_fee or Decimal("0")
        app.fee_hostel    = course.hostel_fee or Decimal("0")
        app.fee_marksheet = course.marksheet_fee or Decimal("0")

        # base subtotal (for info)
        app.fee_base_subtotal = app.fee_admission + app.fee_tuition + app.fee_exam

        # read ALL SIX checkboxes
        add_admission = bool(self.request.POST.get("add_admission"))
        add_tuition   = bool(self.request.POST.get("add_tuition"))
        add_exam      = bool(self.request.POST.get("add_exam"))
        # the other 3 are already on 'app' because they’re model fields bound by the form
        # (app.add_bus, app.add_hostel, app.add_marksheet)

        app.add_admission = add_admission
        app.add_tuition   = add_tuition
        app.add_exam      = add_exam

        # compute selected total
        total = Decimal("0")
        if add_admission: total += app.fee_admission
        if add_tuition:   total += app.fee_tuition
        if add_exam:      total += app.fee_exam
        if app.add_bus:       total += app.fee_bus
        if app.add_hostel:    total += app.fee_hostel
        if app.add_marksheet: total += app.fee_marksheet

        app.fee_selected_total = total
        app.fee_total = total  # keep legacy compatibility
        app.payment_status = "pending"
        app.save()

        return redirect("admissions:review", pk=app.pk)


    
class AdmissionSuccessView(TemplateView):
    template_name = "admissions/success.html"
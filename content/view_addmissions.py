from decimal import Decimal

from django.shortcuts import redirect
from django.views.generic import TemplateView, CreateView

from content.forms import AdmissionApplicationForm
from content.models import Course, AdmissionApplication


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
        form = ctx["form"]

        # 1) Try ?course=... first
        course = None
        course_id = self.request.GET.get("course")
        if course_id:
            course = Course.objects.filter(pk=course_id).first()

        # 2) Fall back to initial desired_course (CreateView form)
        if not course:
            initial_dc = form.initial.get("desired_course")
            # initial might hold a Course instance (because we set it in get_initial)
            if isinstance(initial_dc, Course):
                course = initial_dc
            elif initial_dc:  # id value
                course = Course.objects.filter(pk=initial_dc).first()

        # 3) Lastly, form.instance (rare on CreateView GET, but safe)
        if not course and getattr(form.instance, "desired_course_id", None):
            course = form.instance.desired_course

        ctx["selected_course"] = course

        if course:
            fee_admission = course.admission_fee or Decimal("0")
            fee_tuition   = course.first_month_tuition or Decimal("0")
            fee_exam      = course.exam_fee or Decimal("0")
            # add-ons are unchecked at this point
            fee_bus       = Decimal("0")
            fee_hostel    = Decimal("0")
            fee_marksheet = Decimal("0")

            ctx.update({
                "fee_admission": fee_admission,
                "fee_tuition": fee_tuition,
                "fee_exam": fee_exam,
                "fee_bus": fee_bus,
                "fee_hostel": fee_hostel,
                "fee_marksheet": fee_marksheet,
                "fee_total": fee_admission + fee_tuition + fee_exam
                              + fee_bus + fee_hostel + fee_marksheet,
            })
        else:
            # No course picked yet — keep zeros so the table still renders
            ctx.update({
                "fee_admission": Decimal("0"),
                "fee_tuition": Decimal("0"),
                "fee_exam": Decimal("0"),
                "fee_bus": Decimal("0"),
                "fee_hostel": Decimal("0"),
                "fee_marksheet": Decimal("0"),
                "fee_total": Decimal("0"),
            })
        return ctx

    def form_valid(self, form):
        app = form.save(commit=False)
        course = app.desired_course

        # snapshot base fees from course
        app.fee_admission = course.admission_fee or Decimal("0")
        app.fee_tuition   = course.first_month_tuition or Decimal("0")
        app.fee_exam      = course.exam_fee or Decimal("0")

        # add-ons selected by user (booleans in the form)
        app.fee_bus       = course.bus_fee if app.add_bus else Decimal("0")
        app.fee_hostel    = course.hostel_fee if app.add_hostel else Decimal("0")
        app.fee_marksheet = course.marksheet_fee if app.add_marksheet else Decimal("0")

        app.fee_total = (
            app.fee_admission + app.fee_tuition + app.fee_exam +
            app.fee_bus + app.fee_hostel + app.fee_marksheet
        )

        app.payment_status = "pending"
        app.save()
        return redirect("admissions:review", pk=app.pk)


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
        form = ctx["form"]

        # 1) Try ?course=... first
        course = None
        course_id = self.request.GET.get("course")
        if course_id:
            course = Course.objects.filter(pk=course_id).first()

        # 2) Fall back to initial desired_course (CreateView form)
        if not course:
            initial_dc = form.initial.get("desired_course")
            # initial might hold a Course instance (because we set it in get_initial)
            if isinstance(initial_dc, Course):
                course = initial_dc
            elif initial_dc:  # id value
                course = Course.objects.filter(pk=initial_dc).first()

        # 3) Lastly, form.instance (rare on CreateView GET, but safe)
        if not course and getattr(form.instance, "desired_course_id", None):
            course = form.instance.desired_course

        ctx["selected_course"] = course

        if course:
            fee_admission = course.admission_fee or Decimal("0")
            fee_tuition   = course.first_month_tuition or Decimal("0")
            fee_exam      = course.exam_fee or Decimal("0")
            # add-ons are unchecked at this point
            fee_bus       = Decimal("0")
            fee_hostel    = Decimal("0")
            fee_marksheet = Decimal("0")

            ctx.update({
                "fee_admission": fee_admission,
                "fee_tuition": fee_tuition,
                "fee_exam": fee_exam,
                "fee_bus": fee_bus,
                "fee_hostel": fee_hostel,
                "fee_marksheet": fee_marksheet,
                "fee_total": fee_admission + fee_tuition + fee_exam
                              + fee_bus + fee_hostel + fee_marksheet,
            })
        else:
            # No course picked yet — keep zeros so the table still renders
            ctx.update({
                "fee_admission": Decimal("0"),
                "fee_tuition": Decimal("0"),
                "fee_exam": Decimal("0"),
                "fee_bus": Decimal("0"),
                "fee_hostel": Decimal("0"),
                "fee_marksheet": Decimal("0"),
                "fee_total": Decimal("0"),
            })
        return ctx

    def form_valid(self, form):
        app = form.save(commit=False)
        course = app.desired_course

        # snapshot base fees from course
        app.fee_admission = course.admission_fee or Decimal("0")
        app.fee_tuition   = course.first_month_tuition or Decimal("0")
        app.fee_exam      = course.exam_fee or Decimal("0")

        # add-ons selected by user (booleans in the form)
        app.fee_bus       = course.bus_fee if app.add_bus else Decimal("0")
        app.fee_hostel    = course.hostel_fee if app.add_hostel else Decimal("0")
        app.fee_marksheet = course.marksheet_fee if app.add_marksheet else Decimal("0")

        app.fee_total = (
            app.fee_admission + app.fee_tuition + app.fee_exam +
            app.fee_bus + app.fee_hostel + app.fee_marksheet
        )

        app.payment_status = "pending"
        app.save()
        return redirect("admissions:review", pk=app.pk)


class AdmissionSuccessView(TemplateView):
    template_name = "admissions/success.html"
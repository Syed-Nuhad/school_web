from decimal import Decimal
from time import timezone

from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, CreateView, DetailView

from content.forms import AdmissionApplicationForm
from content.models import Course, AdmissionApplication
from core import settings


class AdmissionApplyView(CreateView):
    model = AdmissionApplication
    form_class = AdmissionApplicationForm
    template_name = "admissions/apply.html"

    def get_initial(self):
        initial = super().get_initial()
        cid = self.request.GET.get("course")
        if cid:
            try:
                initial["desired_course"] = Course.objects.get(pk=cid)
            except Course.DoesNotExist:
                pass
        return initial

    def _resolve_course_from_form(self, form):
        """
        Try to resolve the selected course from:
        1) URL param ?course=
        2) Bound form data (form.data), using the field’s prefixed name
        3) form.initial
        4) form.instance.desired_course
        """
        # 1) URL preselect
        cid = self.request.GET.get("course")
        if cid:
            obj = Course.objects.filter(pk=cid).first()
            if obj:
                return obj

        # 2) Bound form data (works when user changed the select)
        if hasattr(form, "data") and form.data:
            key = form.add_prefix("desired_course")
            cid = form.data.get(key) or form.data.get("desired_course")
            if cid:
                obj = Course.objects.filter(pk=cid).first()
                if obj:
                    return obj

        # 3) form.initial
        dc = form.initial.get("desired_course")
        if isinstance(dc, Course):
            return dc
        if dc:
            obj = Course.objects.filter(pk=dc).first()
            if obj:
                return obj

        # 4) instance
        return getattr(form.instance, "desired_course", None)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = ctx.get("form")
        course = self._resolve_course_from_form(form) if form else None

        ctx["selected_course"] = course

        # Always set fee variables so the template has values.
        fa = ft = fe = Decimal("0.00")
        if course:
            fa = course.admission_fee or Decimal("0.00")
            ft = course.first_month_tuition or Decimal("0.00")
            fe = course.exam_fee or Decimal("0.00")

        ctx["fee_admission"] = fa
        ctx["fee_tuition"]   = ft
        ctx["fee_exam"]      = fe
        ctx["fee_total"]     = fa + ft + fe  # base subtotal shown in the table

        return ctx

    def form_valid(self, form):
        app = form.save(commit=False)
        course = app.desired_course

        # snapshot prices so they don't change later
        app.fee_admission = (course.admission_fee or Decimal("0.00")) if course else Decimal("0.00")
        app.fee_tuition   = (course.first_month_tuition or Decimal("0.00")) if course else Decimal("0.00")
        app.fee_exam      = (course.exam_fee or Decimal("0.00")) if course else Decimal("0.00")
        app.fee_bus       = (course.bus_fee or Decimal("0.00")) if course else Decimal("0.00")
        app.fee_hostel    = (course.hostel_fee or Decimal("0.00")) if course else Decimal("0.00")
        app.fee_marksheet = (course.marksheet_fee or Decimal("0.00")) if course else Decimal("0.00")

        # three core checkboxes are plain inputs in the template
        app.add_admission = bool(self.request.POST.get("add_admission"))
        app.add_tuition   = bool(self.request.POST.get("add_tuition"))
        app.add_exam      = bool(self.request.POST.get("add_exam"))
        # (add_bus/add_hostel/add_marksheet are already bound by the ModelForm)

        # compute selected total (what the user ticked)
        total = Decimal("0.00")
        if app.add_admission: total += app.fee_admission
        if app.add_tuition:   total += app.fee_tuition
        if app.add_exam:      total += app.fee_exam
        if app.add_bus:       total += app.fee_bus
        if app.add_hostel:    total += app.fee_hostel
        if app.add_marksheet: total += app.fee_marksheet

        app.selected_total = total
        app.fee_total = (
            app.fee_admission + app.fee_tuition + app.fee_exam +
            app.fee_bus + app.fee_hostel + app.fee_marksheet
        )
        app.payment_status = "pending"
        app.save()

        # redirect to checkout where you render the dynamic PayPal amount
        return redirect("admissions:checkout", pk=app.pk)


class AdmissionCheckoutView(DetailView):
    model = AdmissionApplication
    template_name = "checkout.html"
    context_object_name = "application"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        app = ctx["application"]

        # Prefer what we stored at form submit:
        total = getattr(app, "fee_total", None)

        # Safety: if not set, recompute from flags + fee snapshots
        if not total or total <= 0:
            total = (
                (app.fee_admission or 0) if app.add_admission else 0
            ) + (
                (app.fee_tuition or 0) if app.add_tuition else 0
            ) + (
                (app.fee_exam or 0) if app.add_exam else 0
            ) + (
                (app.fee_bus or 0) if app.add_bus else 0
            ) + (
                (app.fee_hostel or 0) if app.add_hostel else 0
            ) + (
                (app.fee_marksheet or 0) if app.add_marksheet else 0
            )

        ctx["amount"] = Decimal(total)
        return ctx

class AdmissionSuccessView(TemplateView):
    template_name = "admissions/success.html"


class CheckoutView(DetailView):
    model = AdmissionApplication
    template_name = "admissions/checkout.html"
    context_object_name = "application"


# --- JSON endpoints used by checkout.js / inline JS ---

class PaymentCreateAPI(View):
    """Return the server-calculated amount that must be paid."""
    def get(self, request, pk):
        try:
            app = AdmissionApplication.objects.get(pk=pk)
        except AdmissionApplication.DoesNotExist:
            return HttpResponseBadRequest("Invalid application")
        if app.selected_total <= 0:
            return JsonResponse({"error": "Nothing selected to pay."}, status=400)

        # Adjust currency if you charge in BDT or another currency for PayPal
        return JsonResponse({
            "amount": f"{app.selected_total:.2f}",
            "currency": "USD",
            "description": f"Admission fees for {app.full_name} (#{app.pk})"
        })


class PaymentMarkPaidAPI(View):
    """Mark as paid after provider capture; also send the confirmation email."""
    def post(self, request, pk):
        try:
            app = AdmissionApplication.objects.get(pk=pk)
        except AdmissionApplication.DoesNotExist:
            return HttpResponseBadRequest("Invalid application")

        import json
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")

        # Optionally store payload["provider"], payload["transaction_id"]
        app.payment_status = "paid"
        app.paid_at = timezone.now()
        app.save(update_fields=["payment_status", "paid_at"])

        # Send payment confirmation email (ignore failures silently)
        if app.email:
            try:
                send_mail(
                    subject="Payment Successful",
                    message=(
                        f"Dear {app.full_name},\n\n"
                        f"We have received your payment of {app.selected_total:.2f}.\n"
                        f"Thank you for completing your admission payment.\n\n"
                        f"- Office"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[app.email],
                    fail_silently=True,
                )
            except Exception:
                pass

        return JsonResponse({"ok": True})


class AdmissionSuccessView(TemplateView):
    template_name = "admissions/success.html"




@require_POST
def payment_create(request, pk):
    """
    Returns the exact amount for this application so your PayPal JS
    can create an order with the correct charge (no client-side edits).
    """
    app = get_object_or_404(AdmissionApplication, pk=pk)
    if app.payment_status == "paid":
        return JsonResponse({"ok": False, "error": "Already paid."}, status=400)
    amt = app.selected_total or Decimal("0")
    if amt <= 0:
        return JsonResponse({"ok": False, "error": "Nothing to pay."}, status=400)
    # You can also return currency, description, etc.
    return JsonResponse({
        "ok": True,
        "amount": str(amt),        # keep as string for JS
        "currency": "USD",         # or "BDT" if your PayPal account supports it
        "reference": f"ADM-{app.pk}",
    })


@require_POST
def payment_mark_paid(request, pk):
    """
    Call this AFTER PayPal capture succeeds (server->server or via your JS).
    Marks the application as paid and emails the student.
    """
    app = get_object_or_404(AdmissionApplication, pk=pk)
    if app.payment_status == "paid":
        return JsonResponse({"ok": True, "status": "already_paid"})

    app.payment_status = "paid"
    app.paid_at = timezone.now()
    app.save(update_fields=["payment_status", "paid_at"])

    # Email the student
    recipient = (app.email or "").strip()
    if recipient:
        subject = "Payment Successful – Admission"
        body = (
            f"Dear {app.full_name},\n\n"
            f"We have received your payment for {app.desired_course}.\n"
            f"Amount paid: {app.selected_total}\n"
            f"Application ID: {app.pk}\n\n"
            f"Thank you."
        )
        try:
            send_mail(
                subject,
                body,
                getattr(settings, "DEFAULT_FROM_EMAIL", None) or "no-reply@example.com",
                [recipient],
                fail_silently=True,
            )
        except Exception:
            pass

    return JsonResponse({"ok": True, "status": "paid"})
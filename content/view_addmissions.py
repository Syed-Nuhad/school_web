from decimal import Decimal

from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
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
            c = Course.objects.filter(pk=cid).first()
            if c:
                initial["desired_course"] = c
        return initial

    def form_valid(self, form):
        app = form.save(commit=False)

        # Ensure a course is set (hidden field may be missing)
        if not app.desired_course:
            cid = self.request.GET.get("course")
            if cid:
                app.desired_course = Course.objects.filter(pk=cid).first()
        if not app.desired_course:
            messages.error(self.request, "Please choose a course.")
            return redirect("admissions:apply")

        c = app.desired_course

        # Snapshot course fees NOW so they don’t change later
        app.fee_admission = c.admission_fee or Decimal("0.00")
        app.fee_tuition   = c.first_month_tuition or Decimal("0.00")
        app.fee_exam      = c.exam_fee or Decimal("0.00")
        app.fee_bus       = c.bus_fee or Decimal("0.00")
        app.fee_hostel    = c.hostel_fee or Decimal("0.00")
        app.fee_marksheet = c.marksheet_fee or Decimal("0.00")

        # Three plain checkboxes rendered as <input type="checkbox" name="...">
        app.add_admission = bool(self.request.POST.get("add_admission"))
        app.add_tuition   = bool(self.request.POST.get("add_tuition"))
        app.add_exam      = bool(self.request.POST.get("add_exam"))
        # add_bus/add_hostel/add_marksheet are bound by the ModelForm

        # Calculate what the user actually selected to pay now
        total = Decimal("0.00")
        if app.add_admission: total += app.fee_admission
        if app.add_tuition:   total += app.fee_tuition
        if app.add_exam:      total += app.fee_exam
        if app.add_bus:       total += app.fee_bus
        if app.add_hostel:    total += app.fee_hostel
        if app.add_marksheet: total += app.fee_marksheet

        # ✅ use the correct field names defined in your model
        app.fee_selected_total = total
        app.fee_total = total
        app.payment_status = "pending"

        app.save()
        return redirect("admissions:checkout", pk=app.pk)


class AdmissionCheckoutView(DetailView):
    model = AdmissionApplication
    template_name = "checkout.html"   # make sure this path matches your file
    context_object_name = "application"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        app = ctx["application"]
        course = app.desired_course

        # fallback to course fees when snapshots are zero/blank
        def display(app_fee, course_fee):
            a = app_fee or Decimal("0.00")
            if a > 0:
                return a
            return (course_fee or Decimal("0.00")) if course else Decimal("0.00")

        fa = display(app.fee_admission, getattr(course, "admission_fee", None))
        ft = display(app.fee_tuition,   getattr(course, "first_month_tuition", None))
        fe = display(app.fee_exam,      getattr(course, "exam_fee", None))
        fb = display(app.fee_bus,       getattr(course, "bus_fee", None))
        fh = display(app.fee_hostel,    getattr(course, "hostel_fee", None))
        fm = display(app.fee_marksheet, getattr(course, "marksheet_fee", None))

        # total only the items the user ticked
        selected_total = Decimal("0.00")
        if app.add_admission: selected_total += fa
        if app.add_tuition:   selected_total += ft
        if app.add_exam:      selected_total += fe
        if app.add_bus:       selected_total += fb
        if app.add_hostel:    selected_total += fh
        if app.add_marksheet: selected_total += fm

        # expose display values for the template, and also persist if DB has zeros
        ctx.update({
            "fee_admission_display": fa,
            "fee_tuition_display":   ft,
            "fee_exam_display":      fe,
            "fee_bus_display":       fb,
            "fee_hostel_display":    fh,
            "fee_marksheet_display": fm,
            "selected_total_display": selected_total,
        })

        # one-time repair if your row still has zeros
        needs_save = False
        if (app.fee_admission or 0) == 0 and fa > 0: app.fee_admission = fa; needs_save = True
        if (app.fee_tuition   or 0) == 0 and ft > 0: app.fee_tuition   = ft; needs_save = True
        if (app.fee_exam      or 0) == 0 and fe > 0: app.fee_exam      = fe; needs_save = True
        if (app.fee_bus       or 0) == 0 and fb > 0: app.fee_bus       = fb; needs_save = True
        if (app.fee_hostel    or 0) == 0 and fh > 0: app.fee_hostel    = fh; needs_save = True
        if (app.fee_marksheet or 0) == 0 and fm > 0: app.fee_marksheet = fm; needs_save = True

        if app.fee_selected_total != selected_total:
            app.fee_selected_total = selected_total; needs_save = True
        if app.fee_total != selected_total:
            app.fee_total = selected_total; needs_save = True

        if needs_save:
            app.save(update_fields=[
                "fee_admission","fee_tuition","fee_exam",
                "fee_bus","fee_hostel","fee_marksheet",
                "fee_selected_total","fee_total"
            ])

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
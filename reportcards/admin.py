# reportcards/admin.py
from django import forms
from django.contrib import admin, messages
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Grade, GradeSubject, Term, Marksheet, MarkRow

# ------------------------------------------------------------
# Base admin (reuse OwnableAdminMixin if available)
# ------------------------------------------------------------
try:
    from content.admin import OwnableAdminMixin as BaseAdmin
except Exception:
    class BaseAdmin(admin.ModelAdmin):
        def has_module_permission(self, request): return request.user.is_staff
        def has_view_permission(self, request, obj=None): return request.user.is_staff
        def has_add_permission(self, request): return request.user.is_staff
        def has_change_permission(self, request, obj=None): return request.user.is_staff
        def has_delete_permission(self, request, obj=None): return request.user.is_superuser


# ============================================================
# GRADE + SUBJECTS
# ============================================================
class GradeSubjectInline(admin.TabularInline):
    model = GradeSubject
    fk_name = "grade"
    fields = ("name", "order", "is_active")
    ordering = ("order", "name")
    can_delete = True
    show_change_link = False
    extra = 12  # default 12 blanks

    # Optional: override blanks via ?rows=NN
    def get_extra(self, request, obj=None, **kwargs):
        q = request.GET.get("rows")
        if q:
            try:
                return max(0, min(200, int(q)))
            except Exception:
                pass
        return self.extra


class GradeBulkSubjectsForm(forms.ModelForm):
    bulk_subjects = forms.CharField(
        required=False,
        label="Bulk add subjects",
        widget=forms.Textarea(attrs={
            "rows": 6,
            "placeholder": "One per line (e.g. Mathematics\nEnglish\nPhysics)"
        }),
        help_text="Paste multiple subjects — one per line. Duplicates (case-insensitive) are ignored.",
    )

    class Meta:
        model = Grade
        fields = "__all__"


@admin.register(Grade)
class GradeAdmin(BaseAdmin):
    form = GradeBulkSubjectsForm
    list_display  = ("name", "section", "year")
    list_filter   = ("year",)
    search_fields = ("name", "section")
    ordering      = ("-year", "name", "section")
    inlines       = [GradeSubjectInline]

    fieldsets = (
        (None, {"fields": (("name", "section", "year"),)}),
        ("Bulk add", {"fields": ("bulk_subjects",)}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # ensure obj.id
        raw = (form.cleaned_data.get("bulk_subjects") or "").strip()
        if not raw:
            return

        existing = {
            s.lower()
            for s in GradeSubject.objects.filter(grade=obj).values_list("name", flat=True)
        }
        last_order = GradeSubject.objects.filter(grade=obj).aggregate(Max("order"))["order__max"] or 0

        to_create = []
        for line in raw.splitlines():
            name = line.strip()
            if not name or name.lower() in existing:
                continue
            last_order += 1
            to_create.append(GradeSubject(grade=obj, name=name, order=last_order, is_active=True))

        if to_create:
            GradeSubject.objects.bulk_create(to_create)
            messages.success(request, f"Added {len(to_create)} new subjects to {obj}.")


@admin.register(GradeSubject)
class GradeSubjectAdmin(BaseAdmin):
    list_display  = ("name", "grade", "is_active", "order")
    list_filter   = ("grade", "is_active")
    search_fields = ("name", "grade__name", "grade__section")
    autocomplete_fields = ("grade",)
    ordering = ("grade", "order", "name")


# ============================================================
# TERM
# ============================================================
@admin.register(Term)
class TermAdmin(BaseAdmin):
    list_display  = ("name", "year")
    list_filter   = ("year",)
    search_fields = ("name",)
    ordering      = ("-year", "name")


# ============================================================
# MARKSHEET + ROWS
# ============================================================
class MarkRowInline(admin.TabularInline):
    model = MarkRow
    extra = 0
    # Hide "remark"; show grade_letter read-only
    fields = ("subject", "max_marks", "marks_obtained", "grade_letter", "order")
    readonly_fields = ("grade_letter",)
    autocomplete_fields = ("subject",)
    ordering = ("order", "id")

    # Limit subject choices to the selected grade
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "subject":
            # On add: grade may be in POST/GET; on change: use obj.grade_id (admin passes obj via form construction)
            gid = request.POST.get("grade") or request.GET.get("grade")
            try:
                gid = int(gid) if gid else None
            except Exception:
                gid = None
            if gid:
                kwargs["queryset"] = GradeSubject.objects.filter(
                    grade_id=gid, is_active=True
                ).order_by("order", "name", "id")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None): return request.user.is_staff
    def has_change_permission(self, request, obj=None): return request.user.is_staff
    def has_delete_permission(self, request, obj=None): return request.user.is_staff


class MarksheetAdminForm(forms.ModelForm):
    class Meta:
        model = Marksheet
        fields = "__all__"


@admin.action(description="Reseed subject rows from Grade’s active subjects")
def reseed_rows(modeladmin, request, queryset):
    total = 0
    for ms in queryset.select_related("grade"):
        subjects = (GradeSubject.objects
                    .filter(grade=ms.grade, is_active=True)
                    .order_by("order", "name", "id"))
        existing = set(ms.rows.values_list("subject_id", flat=True))
        order_val = ms.rows.aggregate(Max("order"))["order__max"] or 0

        to_create = []
        for s in subjects:
            if s.id in existing:
                continue
            order_val += 1
            to_create.append(MarkRow(
                marksheet=ms, subject=s, max_marks=100, marks_obtained=0, order=order_val
            ))

        if to_create:
            MarkRow.objects.bulk_create(to_create)
            ms.recalc_totals()
            ms.save(update_fields=["total_obtained", "total_out_of", "percent", "gpa", "grade_letter", "updated_at"])
            total += len(to_create)

    messages.success(request, f"Created {total} missing rows across selected marksheets.")


@admin.register(Marksheet)
class MarksheetAdmin(BaseAdmin):
    form = MarksheetAdminForm
    inlines = [MarkRowInline]
    actions = [reseed_rows]

    list_display  = (
        "student_name", "roll_number", "grade", "term",
        "total_obtained", "total_out_of", "percent", "gpa",
        "grade_letter", "updated_at",
    )
    list_filter   = ("grade", "term", "is_published")
    search_fields = ("student_name", "roll_number")
    autocomplete_fields = ("grade", "term")
    readonly_fields = ("total_obtained", "total_out_of", "percent", "gpa", "grade_letter", "created_at", "updated_at")

    fieldsets = (
        ("Student & Context", {
            "fields": ("student_name", ("roll_number", "section"), "grade", "term", "is_published")
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Totals (auto)", {"fields": ("total_obtained", "total_out_of", "percent", "gpa", "grade_letter")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        creating = not change
        super().save_model(request, obj, form, change)

        # Seed rows on first save (or if none exist)
        if creating or obj.rows.count() == 0:
            subjects = (GradeSubject.objects
                        .filter(grade=obj.grade, is_active=True)
                        .order_by("order", "name", "id"))
            if subjects.exists():
                existing = set(obj.rows.values_list("subject_id", flat=True))
                order_val = obj.rows.aggregate(Max("order"))["order__max"] or 0
                to_create = []
                for s in subjects:
                    if s.id in existing:
                        continue
                    order_val += 1
                    to_create.append(MarkRow(
                        marksheet=obj, subject=s, max_marks=100, marks_obtained=0, order=order_val
                    ))
                if to_create:
                    MarkRow.objects.bulk_create(to_create)

        obj.recalc_totals()
        obj.save(update_fields=["total_obtained", "total_out_of", "percent", "gpa", "grade_letter", "updated_at"])

    # After "Save" on ADD, go to CHANGE so freshly-seeded rows are visible
    def response_add(self, request, obj, post_url_continue=None):
        if "_addanother" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        self.message_user(request, "Marksheet created. Subject rows seeded from the Grade (if any).")
        return HttpResponseRedirect(reverse("admin:reportcards_marksheet_change", args=[obj.pk]))


@admin.register(MarkRow)
class MarkRowAdmin(BaseAdmin):
    list_display  = ("marksheet", "subject", "marks_obtained", "max_marks", "grade_letter", "order")
    list_filter   = ("subject__grade",)
    search_fields = ("marksheet__student_name", "subject__name")
    autocomplete_fields = ("marksheet", "subject")

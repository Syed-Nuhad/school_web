from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django import forms
from .models import Grade, GradeSubject, Term, Marksheet, MarkRow


# -----------------------------
# Grade + subjects (add many at once)
# -----------------------------
class GradeSubjectInline(admin.TabularInline):
    model = GradeSubject
    extra = 12                     # ← shows 12 blank rows to fill at once
    fields = ("name", "is_active", "order")
    ordering = ("order", "name")
    show_change_link = True

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "year")
    list_filter  = ("year",)
    search_fields= ("name", "section")
    ordering     = ("-year", "name", "section")
    inlines      = [GradeSubjectInline]

    # NOTE: Inlines only show on the CHANGE page.
    # So: create the Grade, click Save, then you’ll see the 12 subject rows.


# -----------------------------
# Marksheet + rows
# -----------------------------
class MarkRowInline(admin.TabularInline):
    model = MarkRow
    extra = 12    # ← always show 12 empty rows
    fields = ("subject", "max_marks", "marks_obtained", "grade_letter", "remark", "order")

    # Filter subject choices to the selected Grade (no JS).
    def get_formset(self, request, obj=None, **kwargs):
        # cache the grade id for use in formfield_for_foreignkey
        grade_id = None
        if obj is not None:
            grade_id = obj.grade_id
        else:
            # during "Add", try to read selection
            grade_id = request.POST.get("grade") or request.GET.get("grade")
            if grade_id and str(grade_id).isdigit():
                grade_id = int(grade_id)
            else:
                grade_id = None
        self._selected_grade_id = grade_id
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "subject":
            gid = getattr(self, "_selected_grade_id", None)
            if gid:
                kwargs["queryset"] = GradeSubject.objects.filter(
                    grade_id=gid, is_active=True
                ).order_by("order", "name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # OPTIONAL: Auto-seed rows with all subjects AFTER the first save on Add.
    # Uncomment if you want rows to appear pre-filled (still no JS):
    #
    # def get_formset(self, request, obj=None, **kwargs):
    #     Base = super().get_formset(request, obj, **kwargs)
    #     gid = None
    #     if obj: gid = obj.grade_id
    #     else:
    #         raw = request.POST.get("grade") or request.GET.get("grade")
    #         gid = int(raw) if raw and str(raw).isdigit() else None
    #     self._selected_grade_id = gid
    #
    #     if obj is not None or not gid:
    #         return Base  # edit page or grade not selected yet → default behavior
    #
    #     subjects = GradeSubject.objects.filter(grade_id=gid, is_active=True).order_by("order","name","id")
    #     initial = []
    #     for idx, s in enumerate(subjects, start=1):
    #         initial.append({"subject": s.id, "max_marks": 100, "marks_obtained": 0, "order": idx})
    #
    #     class Seeded(Base):
    #         def __init__(self, *a, **kw):
    #             kw["initial"] = initial
    #             super().__init__(*a, **kw)
    #             self.extra = 0  # only our seeded rows
    #     return Seeded


@admin.register(Marksheet)
class MarksheetAdmin(admin.ModelAdmin):
    inlines = [MarkRowInline]

    list_display  = ("student_name", "roll_number", "grade", "section", "term", "total_obtained", "total_out_of", "percent", "grade_letter", "gpa", "updated_at")
    list_filter   = ("grade", "term", "section", "is_published")
    search_fields = ("student_name", "roll_number")
    autocomplete_fields = ("grade", "term")  # remove this line if you don't use admin autocomplete
    readonly_fields = ("total_obtained", "total_out_of", "percent", "grade_letter", "gpa", "created_at", "updated_at")

    fieldsets = (
        ("Student & Context", {
            "fields": ("student_name", ("roll_number", "section"), "grade", "term")
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Totals (auto)", {"fields": ("total_obtained", "total_out_of", "percent", "grade_letter", "gpa")}),
        ("Visibility & Audit", {"fields": ("is_published", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.recalc_totals()
        obj.save(update_fields=["total_obtained", "total_out_of", "percent", "grade_letter", "gpa", "updated_at"])


@admin.register(GradeSubject)
class GradeSubjectAdmin(admin.ModelAdmin):
    list_display  = ("name", "grade", "is_active", "order")
    list_filter   = ("grade", "is_active")
    search_fields = ("name", "grade__name", "grade__section")
    ordering      = ("grade", "order", "name")


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "year")
    list_filter  = ("year",)
    search_fields= ("name",)
    ordering     = ("-year", "name")
# reportcards/admin.py
from django.contrib import admin
from django import forms
from .models import Grade, GradeSubject, Marksheet, MarkItem

# ----- Inline to enter 12 subjects on the Grade form -----
class GradeSubjectInline(admin.TabularInline):
    model = GradeSubject
    extra = 12                      # <-- shows 12 empty rows right away
    fields = ("name", "order", "is_active")
    ordering = ("order", "name")
    show_change_link = False

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display  = ("name", "section", "year")
    list_filter   = ("year",)
    search_fields = ("name", "section")
    ordering      = ("-year", "name", "section")
    inlines       = [GradeSubjectInline]


# ----- Inline for marksheet items (preload 1 row per GradeSubject) -----
class MarkItemInline(admin.TabularInline):
    model = MarkItem
    extra = 0
    fields = ("subject", "max_marks", "marks_obtained", "grade_letter", "remark", "order")
    autocomplete_fields = ("subject",)

    def _selected_grade_id(self, request, obj):
        # Existing object → use its grade
        if obj is not None and getattr(obj, "grade_id", None):
            return obj.grade_id
        # Add form: POST after choosing grade, or GET ?grade=<id>
        gid = request.POST.get("grade") or request.GET.get("grade")
        try:
            return int(gid) if gid else None
        except (TypeError, ValueError):
            return None

    def get_formset(self, request, obj=None, **kwargs):
        Base = super().get_formset(request, obj, **kwargs)

        # Only preload when adding and we know which grade
        grade_id = self._selected_grade_id(request, obj)
        if obj is not None or not grade_id:
            return Base

        subjects = (GradeSubject.objects
                    .filter(grade_id=grade_id, is_active=True)
                    .order_by("order", "name", "id")
                    .only("id"))

        initial = []
        order = 1
        for s in subjects:
            initial.append({
                "subject": s.id,
                "max_marks": 100,
                "marks_obtained": 0,
                "order": order,
            })
            order += 1

        class PreloadFormSet(Base):
            def __init__(self, *args, **kwargs):
                kwargs["initial"] = initial
                super().__init__(*args, **kwargs)
                self.extra = 0   # don't add blanks on top of our initial rows

        return PreloadFormSet


class MarksheetAdminForm(forms.ModelForm):
    class Meta:
        model = Marksheet
        fields = "__all__"


@admin.register(Marksheet)
class MarksheetAdmin(admin.ModelAdmin):
    form = MarksheetAdminForm
    inlines = [MarkItemInline]

    list_display  = ("student_name", "roll_no", "grade", "term_label",
                     "total_marks", "total_percent", "gpa", "letter_grade", "updated_at")
    list_filter   = ("grade", "term_label")
    search_fields = ("student_name", "roll_no")
    autocomplete_fields = ("grade",)
    readonly_fields = ("total_marks", "total_percent", "gpa", "letter_grade", "created_at", "updated_at")

    fieldsets = (
        ("Student & Context", {
            "fields": ("student_name", ("roll_no", "section"), "grade", "term_label")
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Totals (auto)", {"fields": ("total_marks", "total_percent", "gpa", "letter_grade")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.recalc_totals()
        obj.save(update_fields=["total_marks", "total_percent", "gpa", "letter_grade", "updated_at"])


@admin.register(GradeSubject)
class GradeSubjectAdmin(admin.ModelAdmin):
    list_display  = ("name", "grade", "is_active", "order")
    list_filter   = ("grade", "is_active")
    search_fields = ("name", "grade__name", "grade__section")
    autocomplete_fields = ("grade",)
    ordering = ("grade", "order", "name")


@admin.register(MarkItem)
class MarkItemAdmin(admin.ModelAdmin):
    list_display  = ("marksheet", "subject", "marks_obtained", "max_marks", "grade_letter", "order")
    list_filter   = ("subject__grade",)
    search_fields = ("marksheet__student_name",)
    autocomplete_fields = ("marksheet", "subject")

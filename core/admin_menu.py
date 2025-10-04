from django.contrib import admin
from django.apps import AppConfig


GROUPS = {
    "Admissions": [
        "Course", "AdmissionApplication",
    ],
    "Finance": [
        "IncomeCategory", "ExpenseCategory", "Income", "Expense",
        "TuitionInvoice", "TuitionPayment",
    ],
    "Academics": [
        "AcademicClass", "Subject", "ExamTerm", "TimelineEvent", "ExamRoutine",
    ],
    "Results": [
        "ClassResultSummary", "ClassResultSubjectAvg", "ClassTopper",
        "StudentMarksheet", "StudentMarksheetItem",
    ],
    "Transport": [
        "BusRoute", "BusStop",
    ],
    "Website": [
        "SiteBranding", "FooterSettings", "Banner", "Notice", "AboutSection",
        "GalleryItem", "GalleryPost", "CollegeFestival", "FestivalMedia",
        "ContactInfo", "ContactMessage",
    ],
    "People": [
        "Member",
    ],
}

APP_ORDER = ["Admissions", "Finance", "Academics", "Results", "Transport", "Website", "People"]

def _split_content_app(app_dict):
    """Split the big 'content' app into multiple pseudo-apps by GROUPS."""
    content = app_dict.pop("content", None)
    if not content:
        return []

    existing = {m["object_name"]: m for m in content["models"]}
    used = set()
    apps = []

    for group_name, model_names in GROUPS.items():
        models = [existing[n] for n in model_names if n in existing]
        used.update(n for n in model_names if n in existing)
        if models:
            apps.append({
                "name": group_name,
                "app_label": f"content_{group_name.lower()}",
                "app_url": "",  # no click-through header
                "has_module_perms": True,
                "models": models,
            })

    leftovers = [m for n, m in existing.items() if n not in used]
    if leftovers:
        apps.append({
            "name": "Content (Other)",
            "app_label": "content_other",
            "app_url": "",
            "has_module_perms": True,
            "models": leftovers,
        })
    return apps

def _custom_get_app_list(self, request):
    app_dict = self._build_app_dict(request)
    # split the 'content' app into groups
    apps = _split_content_app(app_dict)
    # keep other apps (reportcards, accounts, auth, etc.)
    apps.extend(app_dict.values())

    # order models within each group by our given order (fallback: name)
    desired_order = {name: i for i, name in enumerate(
        sum(GROUPS.values(), [])  # flatten list
    )}
    for app in apps:
        app["models"].sort(key=lambda m: (desired_order.get(m["object_name"], 999), m["name"].lower()))

    # order the groups themselves
    app_order = {name: i for i, name in enumerate(APP_ORDER)}
    apps.sort(key=lambda a: (app_order.get(a["name"], 999), a["name"].lower()))
    return apps

# apply the patch
admin.site.get_app_list = _custom_get_app_list.__get__(admin.site, admin.AdminSite)





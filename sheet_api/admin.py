from django.contrib import admin

from django.template.response import TemplateResponse
from django.urls import path

from sheet_api import forms
from sheet_api.forms import PuzzleForm
from sheet_api.models import Puzzle, Composer, Work
from sheet_api.scraper.scraper import Parser, InvalidComposer


class MyAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path("scan/", self.admin_view(self.scrape_view))]
        return my_urls + urls

    def scrape_view(self, request):
        form = forms.ScraperAdminForm(request.POST)
        if form.is_valid():
            composer = form.cleaned_data["composer"]
            dry_run = form.cleaned_data["dry_run"]
            print("Got scan request: ", composer, dry_run)
        else:
            print("Form is not valid: ", form.errors)
            return TemplateResponse(
                request,
                "admin/sheet_api/trigger_scan.html",
                {
                    "form_errors": form.errors,
                },
            )

        p = Parser(writes_to_db=not dry_run)

        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
            # Anything else you want in the context...
            # key=value,
        )
        try:
            p.scrape_composer(composer)
        except InvalidComposer:
            context["errors"] = [f"Invalid composer: {composer}"]

        return TemplateResponse(request, "admin/sheet_api/trigger_scan.html", context)

    def index(self, request, extra_context=None):
        # inject my form into the extra_context
        extra_context = extra_context or {}
        extra_context["scraper_form"] = forms.ScraperAdminForm()

        return super().index(request, extra_context)


admin_site = MyAdminSite(name="sheet_api_admin")
admin_site.index_template = "admin/sheet_api/index.html"


def count_of_works(obj):
    return obj.work_set.count()


class ComposerAdmin(admin.ModelAdmin):
    list_display = ("full_name", count_of_works)


class PuzzleAdmin(admin.ModelAdmin):
    form = PuzzleForm

    list_display = ("type", "answer", "difficulty", "date", "sheet_image_url")
    search_fields = ("date", "answer")

    list_filter = ("type", "difficulty")
    ordering = ("type", "date")
    raw_id_fields = ("answer",)


class WorkAdmin(admin.ModelAdmin):
    list_display = (
        "composer",
        "work_title",
        "opus",
        "opus_number",
        "composition_year",
    )
    search_fields = ("work_title", "opus", "opus_number")
    list_filter = ("composer",)
    ordering = ("composer", "composition_year")


# Register your models here.
admin_site.register(Composer, ComposerAdmin)
admin_site.register(Work, WorkAdmin)
admin_site.register(Puzzle, PuzzleAdmin)

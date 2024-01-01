from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from sheet_api.models import Puzzle, Composer, Work
from sheet_api.scraper.scraper import scrape_all_composers


class MyAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path("scan/", self.admin_view(self.my_view))]
        return my_urls + urls

    def my_view(self, request):
        scrape_all_composers()
        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
            # Anything else you want in the context...
            # key=value,
        )
        return TemplateResponse(request, "admin/sheet_api/trigger_scan.html", context)


admin_site = MyAdminSite(name="sheet_api_admin")
admin_site.index_template = "admin/sheet_api/index.html"


def count_of_works(obj):
    return obj.work_set.count()


class ComposerAdmin(admin.ModelAdmin):
    list_display = ("full_name", count_of_works)


class PuzzleAdmin(admin.ModelAdmin):
    list_display = ("type", "answer", "date", "sheet_image_url")
    search_fields = ("date", "answer")

    list_filter = ("type",)
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

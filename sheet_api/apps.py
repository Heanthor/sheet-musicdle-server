from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class SheetApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sheet_api"


class MyAdminConfig(AdminConfig):
    default_site = "sheet_api.admin.MyAdminSite"

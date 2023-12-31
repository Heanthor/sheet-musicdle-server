"""
URL configuration for sheet_musicle_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from sheet_api.admin import admin_site
from django.urls import path, include
from rest_framework import routers

from sheet_api import api_views
from sheet_api.views import trigger_scan

router = routers.DefaultRouter()
router.register(r"users", api_views.UserViewSet)
router.register(r"groups", api_views.GroupViewSet)
router.register(r"puzzles", api_views.PuzzleViewSet)

urlpatterns = [
    path("admin/", admin_site.urls),
    path("admin/scan", trigger_scan),
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

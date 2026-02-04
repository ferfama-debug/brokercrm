from django.contrib import admin
from django.urls import path
import brokercrm.csrf_exempt_admin  # noqa

urlpatterns = [
    path("admin/", admin.site.urls),
]

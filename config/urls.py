from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/licenses/", include("licenses.urls")),
    path("api/vehicles/", include("vehicles.urls")),
    path("api/partnerships/", include("partnerships.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/applications/", include("applications.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/stats/", include("stats.urls")),
    path("api/system/", include("systemsettings.urls")),
    path("api/contact/", include("contact.urls")),
    path("", lambda r: HttpResponse("Backend OK"), name="root"),
    path(
        "debug-info",
        lambda r: JsonResponse(
            {
                "debug": settings.DEBUG,
                "allowed_hosts": settings.ALLOWED_HOSTS,
                "csrf_trusted_origins": settings.CSRF_TRUSTED_ORIGINS,
            }
        ),
        name="debug_info",
    ),
    path("health", lambda r: JsonResponse({"status": "ok"}), name="health"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import health_check

admin.site.site_header = "Сайт Игоря Глушкова"
admin.site.site_title = "Сайт Игоря Глушкова"
admin.site.index_title = "Управление"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/library/", include("apps.library.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

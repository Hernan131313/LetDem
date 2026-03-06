from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse


def health_check(request):
    return HttpResponse('pong')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('ping/', health_check, name='health_check'),
    path('v1/', include('letdem.api_versions.v1.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.landing.urls')),
    path('users/', include('apps.users.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('notifications/', include('apps.notifications.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

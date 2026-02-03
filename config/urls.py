"""URL configuration for the Nexus Django project.

This module defines the root URL routing for the entire application,
including the admin panel, authentication, chat functionality, and
custom error handlers.

Attributes:
    ADMIN_URL_PATH (str): The URL path for the admin panel,
        configurable via environment variable.
    urlpatterns (list): List of URL patterns for the application.
    handler404 (str): Path to the custom 404 error handler.
    handler500 (str): Path to the custom 500 error handler.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.views import index, handler404, handler500
import os

# Admin URL from environment variable (default: admin/)
ADMIN_URL_PATH = os.getenv('ADMIN_URL_PATH', 'admin/')

urlpatterns = [
    path('', index, name='index'),  # Landing page
    path(ADMIN_URL_PATH, admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('chat/', include('chat.urls')),  # Changed from '' to 'chat/'
]

# Custom error handlers
handler404 = 'config.views.handler404'
handler500 = 'config.views.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files from both STATICFILES_DIRS and STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
    if hasattr(settings, 'STATICFILES_DIRS'):
        for static_dir in settings.STATICFILES_DIRS:
            urlpatterns += static(settings.STATIC_URL, document_root=static_dir)
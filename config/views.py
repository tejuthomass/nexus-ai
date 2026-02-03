"""Root views for the Nexus Django application.

This module contains top-level view functions for the landing page
and custom error handlers (404, 500) for the entire application.

Functions:
    index: Renders the landing page with database version info.
    handler404: Custom 404 Not Found error page handler.
    handler500: Custom 500 Internal Server Error handler.
"""

from django.shortcuts import render
from django.db import connection


def index(request):
    """Render the landing page with database version information.

    Queries the connected database for its version information and
    displays it on the landing page. This serves as both a landing
    page and a database connectivity health check.

    Args:
        request: The HttpRequest object for the current request.

    Returns:
        HttpResponse: The rendered index.html template with database
            version in the context.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]

    context = {'db_version': db_version}
    return render(request, 'index.html', context)


def handler404(request, exception=None):
    """Handle 404 Not Found errors with a custom template.

    This handler is triggered when a requested page or resource doesn't
    exist. It renders a user-friendly 404 error page.

    Args:
        request: The HttpRequest object for the current request.
        exception: The exception that triggered the 404 error.
            Defaults to None.

    Returns:
        HttpResponse: The rendered 404.html template with HTTP 404 status.
    """
    return render(request, '404.html', status=404)


def handler500(request):
    """Handle 500 Internal Server errors with a custom template.

    This handler is triggered when an unexpected server error occurs
    during request processing. It renders a user-friendly 500 error page.

    Args:
        request: The HttpRequest object for the current request.

    Returns:
        HttpResponse: The rendered 500.html template with HTTP 500 status.
    """
    return render(request, '500.html', status=500)

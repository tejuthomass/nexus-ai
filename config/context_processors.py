"""Context processors for the Nexus application.

This module provides custom template context processors that inject
additional variables into all template contexts.

Functions:
    admin_url: Adds the admin panel URL path to template context.
"""

import os


def admin_url(request):
    """Add the admin URL path to the template context.

    Retrieves the admin URL path from environment variables, allowing
    the admin panel location to be customized per deployment.

    Args:
        request: The HttpRequest object for the current request.

    Returns:
        dict: A dictionary containing 'admin_url' key with the
            formatted admin panel URL path.

    Example:
        >>> admin_url(request)
        {'admin_url': '/admin/'}
    """
    admin_path = os.getenv('ADMIN_URL_PATH', 'admin/')
    return {
        'admin_url': f'/{admin_path}' if not admin_path.startswith('/') else admin_path,
    }

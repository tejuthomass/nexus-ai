"""
Context processors for Nexus
"""

import os


def admin_url(request):
    """Add admin URL to template context"""
    admin_path = os.getenv('ADMIN_URL_PATH', 'admin/')
    return {
        'admin_url': f'/{admin_path}' if not admin_path.startswith('/') else admin_path,
    }

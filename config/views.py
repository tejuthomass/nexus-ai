from django.shortcuts import render
from django.db import connection


def index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]

    context = {'db_version': db_version}
    return render(request, 'index.html', context)


def handler404(request, exception=None):
    """
    Handle 404 Not Found errors with a custom template.
    This handler is triggered when a requested page/resource doesn't exist.
    """
    return render(request, '404.html', status=404)


def handler500(request):
    """
    Handle 500 Internal Server errors with a custom template.
    This handler is triggered when an unexpected server error occurs.
    """
    return render(request, '500.html', status=500)

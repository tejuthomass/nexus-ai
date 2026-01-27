from django.shortcuts import render
from django.db import connection


def index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]

    context = {'db_version': db_version}
    return render(request, 'index.html', context)

release: python manage.py migrate && python manage.py createcachetable && python manage.py create_superuser_if_missing
web: gunicorn config.wsgi:application

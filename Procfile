release: python manage.py migrate && python manage.py createcachetable
web: gunicorn config.wsgi:application

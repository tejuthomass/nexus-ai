#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

This script is the main entry point for Django management commands.
It loads environment variables from .env before initializing Django.

Usage:
    python manage.py <command> [options]

Common commands:
    runserver: Start the development server.
    migrate: Apply database migrations.
    createsuperuser: Create an admin user.
    collectstatic: Collect static files for production.
    create_superuser_if_missing: Create superuser from env vars.
"""

import os
import sys
import dotenv  # <--- NEW IMPORT


def main():
    """Run administrative tasks for the Django application.

    Loads environment variables from .env file, sets the default
    Django settings module, and executes the requested management
    command.

    Raises:
        ImportError: If Django is not installed or not available
            on the PYTHONPATH.
    """
    # Load environment variables from .env file
    dotenv.load_dotenv()  # <--- NEW COMMAND

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
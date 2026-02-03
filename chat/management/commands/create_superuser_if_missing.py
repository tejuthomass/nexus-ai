"""Management command to create a superuser from environment variables.

This command allows automatic superuser creation on platforms without
shell access (e.g., Render free tier). It reads credentials from
environment variables and creates the superuser only if one does not
already exist with the specified username.

Environment Variables:
    DJANGO_SUPERUSER_USERNAME: The username for the superuser (required).
    DJANGO_SUPERUSER_EMAIL: The email for the superuser (optional).
    DJANGO_SUPERUSER_PASSWORD: The password for the superuser (required).

Usage:
    python manage.py create_superuser_if_missing
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    """Django management command to create a superuser if missing.

    This command checks if a superuser with the specified username
    exists. If not, it creates one using credentials from environment
    variables. This enables automated superuser setup in CI/CD pipelines
    and platform deployments.

    Attributes:
        help (str): Description shown in `manage.py help` output.
    """

    help = "Create a superuser from environment variables if one does not exist"

    def handle(self, *args, **options):
        """Execute the command to create a superuser if needed.

        Reads superuser credentials from environment variables and
        creates the account if it doesn't already exist.

        Args:
            *args: Positional arguments (unused).
            **options: Command options from argparse (unused).

        Returns:
            None: Outputs status messages to stdout.
        """
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping superuser creation: DJANGO_SUPERUSER_USERNAME and "
                    "DJANGO_SUPERUSER_PASSWORD environment variables not set."
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" already exists. Skipping.')
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)

        self.stdout.write(
            self.style.SUCCESS(f'Superuser "{username}" created successfully!')
        )

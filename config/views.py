"""Root views for the Nexus Django application.

This module contains top-level view functions for the landing page,
user signup with invite code verification, and custom error handlers
(404, 500) for the entire application.

Functions:
    index: Renders the landing page with database version info.
    signup: Handles user registration with invite code validation.
    handler404: Custom 404 Not Found error page handler.
    handler500: Custom 500 Internal Server Error handler.
"""

import os

from django.contrib.auth import get_user_model, login
from django.db import connection
from django.shortcuts import redirect, render

User = get_user_model()


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

    context = {"db_version": db_version}
    return render(request, "index.html", context)


def signup(request):
    """Handle user registration with invite code validation.

    This view manages the signup process with three modes based on
    the INVITE_CODE environment variable:
        - Not set: Signup is disabled completely
        - "PUBLIC" (case-sensitive): Signup allowed without invite code
        - Any other value: Requires exact matching invite code

    Args:
        request: The HttpRequest object for the current request.

    Returns:
        HttpResponse: The rendered signup.html template or redirect
            to chat on successful registration.
    """
    # Check if user is already authenticated
    if request.user.is_authenticated:
        return redirect("chat")

    # Get the invite code from environment variable
    invite_code_env = os.environ.get("INVITE_CODE")

    # If INVITE_CODE is not set, signup is disabled
    if invite_code_env is None:
        return render(
            request,
            "registration/signup.html",
            {"signup_disabled": True},
        )

    # Determine if we're in PUBLIC mode (no invite code required)
    is_public_mode = invite_code_env == "PUBLIC"

    context = {
        "signup_disabled": False,
        "require_invite_code": not is_public_mode,
    }

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        invite_code = request.POST.get("invite_code", "")

        # Store form data for repopulating on error
        context["form_data"] = {"username": username, "email": email}

        # Validate invite code if not in PUBLIC mode
        if not is_public_mode:
            if invite_code != invite_code_env:
                context["error"] = "Invalid invite code"
                return render(request, "registration/signup.html", context)

        # Validate required fields
        if not username:
            context["error"] = "Username is required"
            return render(request, "registration/signup.html", context)

        if not email:
            context["error"] = "Email is required"
            return render(request, "registration/signup.html", context)

        if not password:
            context["error"] = "Password is required"
            return render(request, "registration/signup.html", context)

        # Validate password match
        if password != password_confirm:
            context["error"] = "Passwords do not match"
            return render(request, "registration/signup.html", context)

        # Validate password length
        if len(password) < 8:
            context["error"] = "Password must be at least 8 characters"
            return render(request, "registration/signup.html", context)

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            context["error"] = "Username already exists"
            return render(request, "registration/signup.html", context)

        # Check if email already exists (only check non-empty emails)
        if email and User.objects.filter(email=email).exists():
            context["error"] = "Email already registered"
            return render(request, "registration/signup.html", context)

        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            # Log the user in
            login(request, user)
            return redirect("chat")
        except Exception:
            context["error"] = "An error occurred. Please try again."
            return render(request, "registration/signup.html", context)

    return render(request, "registration/signup.html", context)


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
    return render(request, "404.html", status=404)


def handler500(request):
    """Handle 500 Internal Server errors with a custom template.

    This handler is triggered when an unexpected server error occurs
    during request processing. It renders a user-friendly 500 error page.

    Args:
        request: The HttpRequest object for the current request.

    Returns:
        HttpResponse: The rendered 500.html template with HTTP 500 status.
    """
    return render(request, "500.html", status=500)

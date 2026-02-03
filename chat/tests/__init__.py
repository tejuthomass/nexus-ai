"""Test suite for the Nexus chat application.

This package contains comprehensive Django tests for the chat application,
organized into separate modules for better maintainability:

Modules:
    test_models: Tests for ChatSession, Message, and Document models.
    test_views: Tests for all view functions and API endpoints.
    test_middleware: Tests for rate limiting middleware.
    test_utils: Tests for utility functions (RAG, model fallback).

Usage:
    Run all chat tests:
        python manage.py test chat

    Run specific test module:
        python manage.py test chat.tests.test_models

    Run specific test class:
        python manage.py test chat.tests.test_models.ChatSessionModelTest

    Run with verbosity:
        python manage.py test chat -v 2
"""

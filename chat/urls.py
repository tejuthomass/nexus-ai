"""URL configuration for the chat application.

This module defines URL patterns for chat-related functionality including:
    - Main chat interface and session management
    - Document uploads and chat message handling
    - Admin dashboard for user and session management
    - API endpoints for chat data and service availability

URL Patterns:
    '' : Main chat view (redirects to latest session)
    '<session_id>/' : View specific chat session
    'new/' : Create a new chat session
    '<session_id>/delete/' : Delete a user's chat session
    '<session_id>/rename/' : Rename a chat session
    'dashboard/' : Admin dashboard
    'dashboard/user/<user_id>/delete/' : Delete a user (admin)
    'dashboard/chat/<session_id>/delete/' : Delete any session (admin)
    'dashboard/chat/<session_id>/view/' : View session read-only (admin)
    'api/admin-chat/<session_id>/' : Get chat data as JSON (admin)
    'api/check-availability/' : Check AI service availability
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_view, name="chat"),
    path("<int:session_id>/", views.chat_view, name="chat_session"),
    path("new/", views.new_chat, name="new_chat"),
    path(
        "<int:session_id>/delete/",
        views.delete_user_chat_session,
        name="delete_user_chat_session",
    ),
    path("<int:session_id>/rename/", views.rename_chat, name="rename_chat"),
    path("dashboard/", views.admin_dashboard, name="dashboard"),
    path("dashboard/user/<int:user_id>/delete/", views.delete_user, name="delete_user"),
    path(
        "dashboard/chat/<int:session_id>/delete/",
        views.delete_chat_session,
        name="delete_chat_session",
    ),
    path(
        "dashboard/chat/<int:session_id>/view/",
        views.view_chat_readonly,
        name="view_chat_readonly",
    ),
    path(
        "api/admin-chat/<int:session_id>/", views.api_admin_chat, name="api_admin_chat"
    ),
    path(
        "api/check-availability/", views.check_availability, name="check_availability"
    ),
]

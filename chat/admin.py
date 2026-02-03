"""Django admin configuration for the chat application.

This module registers and configures the admin interface for chat-related
models including ChatSession, Message, and Document. It provides customized
list displays, filters, search capabilities, and read-only fields.

Classes:
    ChatSessionAdmin: Admin configuration for ChatSession model.
    MessageAdmin: Admin configuration for Message model.
    DocumentAdmin: Admin configuration for Document model.
"""

from django.contrib import admin
from .models import ChatSession, Message, Document


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Admin configuration for the ChatSession model.

    Provides a customized admin interface for managing chat sessions
    with filtering, searching, and date hierarchy navigation.

    Attributes:
        list_display (tuple): Fields to display in the list view.
        list_filter (tuple): Fields to filter by in the sidebar.
        search_fields (tuple): Fields to search in.
        date_hierarchy (str): Field for date-based navigation.
        ordering (tuple): Default ordering for the list view.
        readonly_fields (tuple): Fields that cannot be edited.
    """

    list_display = ("id", "user", "title", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at", "user")
    search_fields = ("title", "user__username")
    date_hierarchy = "created_at"
    ordering = ("-updated_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for the Message model.

    Provides a customized admin interface for managing chat messages
    with a content preview, filtering by role and date, and search
    capabilities.

    Attributes:
        list_display (tuple): Fields to display in the list view.
        list_filter (tuple): Fields to filter by in the sidebar.
        search_fields (tuple): Fields to search in.
        date_hierarchy (str): Field for date-based navigation.
        ordering (tuple): Default ordering for the list view.
        readonly_fields (tuple): Fields that cannot be edited.
    """

    list_display = ("id", "session", "role", "content_preview", "created_at")
    list_filter = ("role", "created_at", "session__user")
    search_fields = ("content", "session__title")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    def content_preview(self, obj):
        """Generate a truncated preview of the message content.

        Args:
            obj: The Message model instance.

        Returns:
            str: The first 50 characters of the message content,
                with ellipsis if truncated.
        """
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content Preview"


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin configuration for the Document model.

    Provides a customized admin interface for managing uploaded
    documents with filtering by date and user, and search capabilities.

    Attributes:
        list_display (tuple): Fields to display in the list view.
        list_filter (tuple): Fields to filter by in the sidebar.
        search_fields (tuple): Fields to search in.
        date_hierarchy (str): Field for date-based navigation.
        ordering (tuple): Default ordering for the list view.
        readonly_fields (tuple): Fields that cannot be edited.
    """

    list_display = ("id", "session", "title", "uploaded_at")
    list_filter = ("uploaded_at", "session__user")
    search_fields = ("title", "session__title")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)
    readonly_fields = ("uploaded_at",)

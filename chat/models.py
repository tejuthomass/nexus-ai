"""Database models for the Nexus chat application.

This module defines the core data models for the chat functionality:
- ChatSession: Represents a conversation thread owned by a user.
- Document: Represents an uploaded PDF document attached to a session.
- Message: Represents a single message (user or assistant) in a session.

The models support RAG (Retrieval-Augmented Generation) by linking
documents to specific chat sessions for context-aware responses.
"""

import markdown
import re
import html as html_module
from django.db import models
from django.contrib.auth.models import User
from django.utils.html import escape


class ChatSession(models.Model):
    """Represents a chat conversation session.

    A ChatSession is a conversation thread owned by a user. It contains
    multiple messages and can have documents attached for RAG-based Q&A.
    Sessions are ordered by last update time to show recent conversations first.

    Attributes:
        user (ForeignKey): The user who owns this chat session.
        title (str): The display title of the session (max 200 chars).
        created_at (datetime): When the session was created.
        updated_at (datetime): When the session was last modified.

    Meta:
        ordering: Sessions are ordered by most recently updated first.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    # We will sort by this to show the latest chat at the top
    updated_at = models.DateTimeField(auto_now=True) 
    
    class Meta:
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['user', '-updated_at']),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        """Return the string representation of the chat session.

        Returns:
            str: The title of the chat session.
        """
        return f"{self.title}"


class Document(models.Model):
    """Represents an uploaded document attached to a chat session.

    Documents are PDF files uploaded by users for RAG-based Q&A.
    Each document is linked to a specific chat session, ensuring
    privacy between different conversations.

    Attributes:
        session (ForeignKey): The chat session this document belongs to.
        file (FileField): The uploaded file stored in cloud storage.
        title (str): The display name of the document (max 255 chars).
        uploaded_at (datetime): When the document was uploaded.

    Meta:
        ordering: Documents are ordered by most recently uploaded first.
    """

    # Link to Session, not just User.
    # This means files are "inside" a specific chat thread.
    session = models.ForeignKey(ChatSession, related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to='pdfs/')
    title = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for the Document model."""

        indexes = [
            models.Index(fields=['session', '-uploaded_at']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        """Return the string representation of the document.

        Returns:
            str: The title of the document.
        """
        return self.title


class Message(models.Model):
    """Represents a single message in a chat session.

    Messages can be from either the user or the AI assistant (Nexus).
    Assistant messages include metadata about which AI model generated
    the response.

    Attributes:
        SESSION_ROLES (list): Valid role choices for messages.
        session (ForeignKey): The chat session this message belongs to.
        role (str): Either 'user' or 'assistant'.
        content (str): The text content of the message.
        model_used (str): The AI model that generated this response
            (only for assistant messages).
        created_at (datetime): When the message was created.

    Meta:
        ordering: Messages are ordered chronologically.
    """

    SESSION_ROLES = [('user', 'User'), ('assistant', 'Nexus')]

    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=SESSION_ROLES)
    content = models.TextField()
    model_used = models.CharField(max_length=100, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for the Message model."""

        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
        ordering = ['created_at']

    def get_html_content(self):
        """Render the message content as HTML with Markdown formatting.

        Converts Markdown-formatted text to HTML with support for:
        - Bold, italic, and other inline formatting
        - Code blocks with syntax highlighting
        - Tables, lists, and blockquotes
        - Automatic line break conversion

        Returns:
            str: The message content rendered as safe HTML.
        """
        content = self.content or ""
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Render markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=[
                'extra',           # Includes tables, footnotes, abbr, etc.
                'fenced_code',     # Support for ``` code blocks
                'codehilite',      # Syntax highlighting in code blocks
                'tables',          # Table support
                'nl2br',           # Convert newlines to <br> tags for readability
                'sane_lists',      # Better list handling
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                    'guess_lang': True,
                }
            },
            output_format='html5'
        )
        
        return html_content
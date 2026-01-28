import markdown
import re
import html as html_module
from django.db import models
from django.contrib.auth.models import User
from django.utils.html import escape

class ChatSession(models.Model):
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
        return f"{self.title}"

class Document(models.Model):
    # CHANGED: Link to Session, not just User. 
    # This means files are "inside" a specific chat thread.
    session = models.ForeignKey(ChatSession, related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to='pdfs/') 
    title = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session', '-uploaded_at']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

class Message(models.Model):
    SESSION_ROLES = [('user', 'User'), ('assistant', 'Nexus')]
    
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=SESSION_ROLES)
    content = models.TextField()
    model_used = models.CharField(max_length=100, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
        ordering = ['created_at']
    
    def get_html_content(self):
        """
        Render markdown with robust extensions for proper formatting.
        Handles bold, italic, lists, code blocks, tables, and more.
        """
        # First, clean the content to ensure proper formatting
        content = self.content or ""
        
        # Remove extra asterisks that aren't part of markdown syntax
        # This handles cases like *** or **** which should be single emphasis markers
        content = re.sub(r'\*{4,}', '***', content)
        
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
                'toc',             # Table of contents (optional but useful)
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                }
            },
            output_format='html5'
        )
        
        return html_content
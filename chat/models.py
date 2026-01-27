import markdown
from django.db import models
from django.contrib.auth.models import User

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
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
        ordering = ['created_at']
    
    def get_html_content(self):
        """Render markdown with robust extensions so bullets, bold, and code render cleanly."""
        return markdown.markdown(
            self.content or "",
            extensions=[
                'extra',        # tables, code fences, etc.
                'fenced_code',
                'codehilite',
                'tables',
                'nl2br',
                'sane_lists',
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                }
            },
            output_format='html5'
        )
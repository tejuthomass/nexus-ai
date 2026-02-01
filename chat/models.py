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
        content = self.content or ""
        
        # ===== PREPROCESSING TO FIX COMMON MARKDOWN EDGE CASES =====
        
        # 1. Fix excessive asterisks (e.g., **** or *** that aren't horizontal rules)
        content = re.sub(r'\*{4,}', '**', content)
        
        # 2. Fix malformed bold: ** text** or **text ** (spaces inside markers)
        content = re.sub(r'\*\*\s+([^*]+?)\s+\*\*', r'**\1**', content)
        content = re.sub(r'\*\*\s+([^*]+?)\*\*', r'**\1**', content)
        content = re.sub(r'\*\*([^*]+?)\s+\*\*', r'**\1**', content)
        
        # 3. Fix malformed italic: * text* or *text * 
        content = re.sub(r'(?<!\*)\*\s+([^*]+?)\s+\*(?!\*)', r'*\1*', content)
        content = re.sub(r'(?<!\*)\*\s+([^*]+?)\*(?!\*)', r'*\1*', content)
        content = re.sub(r'(?<!\*)\*([^*]+?)\s+\*(?!\*)', r'*\1*', content)
        
        # 4. Fix unclosed backticks for inline code (odd number of backticks)
        # Count backticks, if odd, escape the last one
        backtick_count = content.count('`') - content.count('```') * 3
        if backtick_count % 2 != 0:
            # Find the last single backtick and escape it
            content = re.sub(r'`([^`]*)$', r'`\1`', content)
        
        # 5. Fix asterisks that are clearly not markdown (e.g., "5 * 3 = 15")
        # Math expressions: number * number
        content = re.sub(r'(\d)\s*\*\s*(\d)', r'\1 × \2', content)
        
        # 6. Ensure code blocks have proper newlines
        content = re.sub(r'```(\w+)?([^\n])', r'```\1\n\2', content)
        content = re.sub(r'([^\n])```', r'\1\n```', content)
        
        # 7. Fix bullet points that might have extra asterisks
        content = re.sub(r'^\*{2,}\s+', '* ', content, flags=re.MULTILINE)
        
        # 8. Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # ===== RENDER MARKDOWN TO HTML =====
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
                }
            },
            output_format='html5'
        )
        
        # ===== POST-PROCESSING TO CATCH REMAINING ISSUES =====
        
        # Fix any remaining raw asterisks that weren't converted
        # Single asterisks surrounded by spaces (not part of markdown)
        html_content = re.sub(r'\s\*\s', ' • ', html_content)
        
        # Fix any remaining backticks that weren't converted to code
        # (This catches edge cases the markdown parser missed)
        html_content = re.sub(r'`([^`<>]+)`', r'<code>\1</code>', html_content)
        
        return html_content
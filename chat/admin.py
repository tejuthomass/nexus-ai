from django.contrib import admin
from .models import ChatSession, Message, Document

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at', 'session__user')
    search_fields = ('content', 'session__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'title', 'uploaded_at')
    list_filter = ('uploaded_at', 'session__user')
    search_fields = ('title', 'session__title')
    date_hierarchy = 'uploaded_at'
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)

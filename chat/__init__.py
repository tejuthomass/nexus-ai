"""Chat application package for Nexus.

This package implements the core AI-powered chat functionality including:
- User chat sessions and message handling
- Document upload and RAG (Retrieval-Augmented Generation)
- Multi-model AI response generation with fallback
- Rate limiting and API protection
- Admin dashboard and user management

Modules:
    models: Database models for chat sessions, messages, and documents.
    views: View functions for chat interface and API endpoints.
    admin: Django admin configuration for chat models.
    apps: Django app configuration.
    middleware: Rate limiting middleware classes.
    model_fallback: Multi-model AI response generation with fallback.
    rag: Retrieval-Augmented Generation for document-based Q&A.
    signals: Django signals for cleanup operations.
    urls: URL routing for chat endpoints.
"""

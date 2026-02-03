# pylint: disable=unused-argument

"""Django signals for chat model cleanup operations.

This module registers signal handlers to perform cleanup when chat
models are deleted. It ensures associated resources (Cloudinary files,
Pinecone vectors) are properly cleaned up to prevent orphaned data.

Signal Handlers:
    cleanup_user_data: Pre-delete handler for User model.
    cleanup_session_data: Pre-delete handler for ChatSession model.
    cleanup_document_file: Post-delete handler for Document model.
    cleanup_message_data: Post-delete handler for Message model.

The cleanup cascade:
    User deletion → Session cleanup (vectors) → Document cleanup (Cloudinary)
    Session deletion → Document cleanup (via CASCADE) → Vector cleanup
    Document deletion → Cloudinary file cleanup
"""

import logging

import cloudinary.uploader
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .models import ChatSession, Document, Message
from .rag import delete_session_vectors

User = get_user_model()

logger = logging.getLogger(__name__)


# 0. Trigger when a USER is deleted - cleanup all user's PDFs from Cloudinary
@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up all user data before user deletion.

    This pre-delete signal handler runs before Django's CASCADE delete.
    It cleans up Pinecone vectors for all user sessions. Cloudinary
    file cleanup is handled automatically by Document post_delete signals
    when CASCADE deletes the documents.

    Args:
        sender: The model class (User).
        instance: The User instance being deleted.
        **kwargs: Additional keyword arguments from the signal.
    """
    logger.info(
        "🗑️ Preparing to delete user '%s' and all associated data",
        instance.username,
    )

    # Get all sessions for this user
    sessions = ChatSession.objects.filter(user=instance)
    session_count = sessions.count()

    if session_count > 0:
        logger.info(
            "Found %s sessions to clean up for user %s",
            session_count,
            instance.username,
        )

        # Clean Pinecone vectors for each session before cascade deletes them
        for session in sessions:
            doc_count = Document.objects.filter(session=session).count()
            if doc_count > 0:
                logger.info(
                    "Session %s has %s documents (Cloudinary cleanup via CASCADE)",
                    session.id,
                    doc_count,
                )

            # Clean Pinecone vectors for this session
            cleanup_success = delete_session_vectors(session.id)
            if not cleanup_success:
                logger.warning("⚠️ Vectors may be orphaned for session %s", session.id)

    logger.info(
        "✅ User %s pre-delete cleanup completed (CASCADE will handle documents)",
        instance.username,
    )


# 1. Trigger when a SESSION is deleted - handles cascade cleanup with retry logic
@receiver(pre_delete, sender=ChatSession)
def cleanup_session_data(sender, instance, **kwargs):
    """Clean up session data before session deletion.

    Deletes Pinecone vectors associated with the session. Document
    cleanup is handled by Django CASCADE triggering Document post_delete
    signals. Logs warnings if vector cleanup fails but does not block
    session deletion.

    Args:
        sender: The model class (ChatSession).
        instance: The ChatSession instance being deleted.
        **kwargs: Additional keyword arguments from the signal.
    """
    logger.info(
        "🗑️ Preparing to delete session '%s' (ID: %s)",
        instance.title,
        instance.id,
    )

    # Count documents for logging (actual deletion happens via CASCADE + Document signal)
    doc_count = Document.objects.filter(session=instance).count()
    if doc_count > 0:
        logger.info("Found %s documents to clean up", doc_count)
        # Documents will be deleted by CASCADE, triggering their post_delete signal
        # which handles Cloudinary cleanup - no need to manually delete here

    # Clean Pinecone Vectors with retry logic
    cleanup_success = delete_session_vectors(instance.id)

    if not cleanup_success:
        # Vector cleanup failed - create an orphaned vectors tracking log
        # This allows admins to manually clean up later or implement a cleanup job
        logger.critical(
            "⚠️ SESSION DELETED BUT VECTORS MAY BE ORPHANED: "
            "Session ID: %s, Title: '%s', User: %s. "
            "RECOMMEND: Manual Pinecone cleanup with filter session_id=%s",
            instance.id,
            instance.title,
            instance.user.username,
            instance.id,
        )
        # Note: We don't raise an exception here to prevent blocking the session deletion
        # The session will be deleted, but vectors may remain (orphaned)
        # This is better than preventing deletion entirely

    logger.info(
        "✅ Session %s cleanup completed (vectors %s)",
        instance.id,
        "cleaned" if cleanup_success else "MAY BE ORPHANED",
    )


# 2. Trigger when a DOCUMENT is deleted
@receiver(post_delete, sender=Document)
def cleanup_document_file(sender, instance, **kwargs):
    """Clean up Cloudinary file after document deletion.

    Deletes the associated file from Cloudinary storage. Uses retry
    logic with up to 3 attempts for reliability. PDFs are stored as
    'raw' resource type in Cloudinary.

    Args:
        sender: The model class (Document).
        instance: The Document instance that was deleted.
        **kwargs: Additional keyword arguments from the signal.
    """
    logger.info("☁️ Cleaning up document: %s", instance.title)

    # Clean Cloudinary File with retry logic
    if instance.file:
        public_id = instance.file.name
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # PDFs are stored as 'raw' resource type in Cloudinary
                result = cloudinary.uploader.destroy(public_id, resource_type="raw")
                if result.get("result") == "ok":
                    logger.info("✅ Deleted Cloudinary file: %s", public_id)
                    break
                elif result.get("result") == "not found":
                    logger.warning(
                        "⚠️ Cloudinary file not found (may already be deleted): %s",
                        public_id,
                    )
                    break
                else:
                    logger.warning("Cloudinary deletion returned: %s", result)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "Retry %s/%s for Cloudinary deletion: %s",
                        attempt + 1,
                        max_retries,
                        e,
                    )
                else:
                    logger.error(
                        "❌ Failed to delete Cloudinary file after %s attempts: %s - %s",
                        max_retries,
                        public_id,
                        e,
                    )


# 3. Trigger when MESSAGES are deleted (cascade from session deletion)
@receiver(post_delete, sender=Message)
def cleanup_message_data(sender, instance, **kwargs):
    """Log message deletion for debugging purposes.

    Currently only logs the deletion. Messages have no external
    resources to clean up.

    Args:
        sender: The model class (Message).
        instance: The Message instance that was deleted.
        **kwargs: Additional keyword arguments from the signal.
    """
    logger.debug(
        "Message deleted: %s from session %s", instance.id, instance.session_id
    )

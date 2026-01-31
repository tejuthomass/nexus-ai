from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ChatSession, Document, Message
from .rag import delete_session_vectors
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

# 0. Trigger when a USER is deleted - cleanup all user's PDFs from Cloudinary
@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    When admin deletes a user, ensure all their PDFs are deleted from Cloudinary.
    Django CASCADE will handle the database cleanup, and Document post_delete
    signals will handle Cloudinary file deletion automatically.
    We just need to clean Pinecone vectors here before cascade happens.
    """
    logger.info(f"🗑️ Preparing to delete user '{instance.username}' and all associated data")
    
    # Get all sessions for this user
    sessions = ChatSession.objects.filter(user=instance)
    session_count = sessions.count()
    
    if session_count > 0:
        logger.info(f"Found {session_count} sessions to clean up for user {instance.username}")
        
        # Clean Pinecone vectors for each session before cascade deletes them
        for session in sessions:
            doc_count = Document.objects.filter(session=session).count()
            if doc_count > 0:
                logger.info(f"Session {session.id} has {doc_count} documents (Cloudinary cleanup via CASCADE)")
            
            # Clean Pinecone vectors for this session
            cleanup_success = delete_session_vectors(session.id)
            if not cleanup_success:
                logger.warning(f"⚠️ Vectors may be orphaned for session {session.id}")
    
    logger.info(f"✅ User {instance.username} pre-delete cleanup completed (CASCADE will handle documents)")

# 1. Trigger when a SESSION is deleted - handles cascade cleanup with retry logic
@receiver(pre_delete, sender=ChatSession)
def cleanup_session_data(sender, instance, **kwargs):
    logger.info(f"🗑️ Preparing to delete session '{instance.title}' (ID: {instance.id})")
    
    # Count documents for logging (actual deletion happens via CASCADE + Document signal)
    doc_count = Document.objects.filter(session=instance).count()
    if doc_count > 0:
        logger.info(f"Found {doc_count} documents to clean up")
        # Documents will be deleted by CASCADE, triggering their post_delete signal
        # which handles Cloudinary cleanup - no need to manually delete here
    
    # Clean Pinecone Vectors with retry logic
    cleanup_success = delete_session_vectors(instance.id)
    
    if not cleanup_success:
        # Vector cleanup failed - create an orphaned vectors tracking log
        # This allows admins to manually clean up later or implement a cleanup job
        logger.critical(
            f"⚠️ SESSION DELETED BUT VECTORS MAY BE ORPHANED: "
            f"Session ID: {instance.id}, Title: '{instance.title}', User: {instance.user.username}. "
            f"RECOMMEND: Manual Pinecone cleanup with filter session_id={instance.id}"
        )
        # Note: We don't raise an exception here to prevent blocking the session deletion
        # The session will be deleted, but vectors may remain (orphaned)
        # This is better than preventing deletion entirely
    
    logger.info(f"✅ Session {instance.id} cleanup completed (vectors {'cleaned' if cleanup_success else 'MAY BE ORPHANED'})")

# 2. Trigger when a DOCUMENT is deleted
@receiver(post_delete, sender=Document)
def cleanup_document_file(sender, instance, **kwargs):
    logger.info(f"☁️ Cleaning up document: {instance.title}")
    
    # Clean Cloudinary File with retry logic
    if instance.file:
        public_id = instance.file.name
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # PDFs are stored as 'raw' resource type in Cloudinary
                result = cloudinary.uploader.destroy(public_id, resource_type="raw")
                if result.get('result') == 'ok':
                    logger.info(f"✅ Deleted Cloudinary file: {public_id}")
                    break
                elif result.get('result') == 'not found':
                    logger.warning(f"⚠️ Cloudinary file not found (may already be deleted): {public_id}")
                    break
                else:
                    logger.warning(f"Cloudinary deletion returned: {result}")
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for Cloudinary deletion: {e}")
                else:
                    logger.error(f"❌ Failed to delete Cloudinary file after {max_retries} attempts: {public_id} - {e}")

# 3. Trigger when MESSAGES are deleted (cascade from session deletion)
@receiver(post_delete, sender=Message)
def cleanup_message_data(sender, instance, **kwargs):
    logger.debug(f"Message deleted: {instance.id} from session {instance.session_id}")

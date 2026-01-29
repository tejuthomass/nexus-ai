from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from .models import ChatSession, Document, Message
from .rag import delete_session_vectors
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

# 1. Trigger when a SESSION is deleted - handles cascade cleanup
@receiver(pre_delete, sender=ChatSession)
def cleanup_session_data(sender, instance, **kwargs):
    logger.info(f"🗑️ Preparing to delete session '{instance.title}' (ID: {instance.id})")
    
    # Get all documents before deletion
    documents = Document.objects.filter(session=instance)
    doc_count = documents.count()
    
    if doc_count > 0:
        logger.info(f"Found {doc_count} documents to clean up")
        # Delete each document (which triggers its own cleanup signal)
        for doc in documents:
            doc.delete()
    
    # Clean Pinecone Vectors
    try:
        delete_session_vectors(instance.id)
    except Exception as e:
        logger.error(f"Error deleting session vectors: {e}")
    
    logger.info(f"✅ Session {instance.id} cleanup completed")

# 2. Trigger when a DOCUMENT is deleted
@receiver(post_delete, sender=Document)
def cleanup_document_file(sender, instance, **kwargs):
    logger.info(f"☁️ Cleaning up document: {instance.title}")
    
    # Clean Cloudinary File
    if instance.file:
        try:
            # We stored the public_id in the file name field
            public_id = instance.file.name 
            cloudinary.uploader.destroy(public_id, resource_type="auto")
            logger.info(f"✅ Deleted Cloudinary file: {public_id}")
        except Exception as e:
            logger.error(f"Error deleting from Cloudinary: {e}")

# 3. Trigger when MESSAGES are deleted (cascade from session deletion)
@receiver(post_delete, sender=Message)
def cleanup_message_data(sender, instance, **kwargs):
    logger.debug(f"Message deleted: {instance.id} from session {instance.session_id}")

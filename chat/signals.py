from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ChatSession, Document
from .rag import delete_session_vectors
import cloudinary.uploader

# 1. Trigger when a SESSION is deleted
@receiver(post_delete, sender=ChatSession)
def cleanup_session_data(sender, instance, **kwargs):
    print(f"🗑️ Session '{instance.title}' deleted. Cleaning up...")
    
    # Clean Pinecone Vectors
    delete_session_vectors(instance.id)

# 2. Trigger when a DOCUMENT is deleted
@receiver(post_delete, sender=Document)
def cleanup_document_file(sender, instance, **kwargs):
    # Clean Cloudinary File
    if instance.file:
        try:
            # We stored the public_id in the file name field
            public_id = instance.file.name 
            cloudinary.uploader.destroy(public_id, resource_type="auto")
            print(f"☁️ Deleted Cloudinary file: {public_id}")
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
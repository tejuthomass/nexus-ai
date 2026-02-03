"""Django app configuration for the chat application.

This module defines the ChatConfig class which configures the chat
application and sets up signal handlers on application ready.
"""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Configuration class for the chat Django application.

    This class configures the chat app settings and initializes
    signal handlers when the application is ready.

    Attributes:
        default_auto_field (str): The default primary key field type
            for models in this app.
        name (str): The name of the application.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        """Initialize the chat application.

        Called when Django starts and the app is ready. This method
        imports the signals module to register signal handlers for
        cleanup operations (Cloudinary, Pinecone vector deletion).
        """
        import chat.signals  # <--- Add this line
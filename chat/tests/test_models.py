"""Tests for chat application models.

This module tests the ChatSession, Message, and Document models including:
    - Model creation and field validation
    - Model relationships and cascading deletes
    - Model methods (e.g., __str__, get_html_content)
    - Model ordering and constraints
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch, MagicMock
from chat.models import ChatSession, Message, Document
import time

# Use local file storage for tests instead of Cloudinary
TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


class ChatSessionModelTest(TestCase):
    """Test cases for the ChatSession model."""

    def setUp(self):
        """Set up test data for ChatSession tests."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_chat_session(self):
        """Test that a ChatSession can be created with default values."""
        session = ChatSession.objects.create(user=self.user)

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.title, "New Chat")
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.updated_at)

    def test_create_chat_session_with_title(self):
        """Test creating a ChatSession with a custom title."""
        session = ChatSession.objects.create(user=self.user, title="My Custom Chat")

        self.assertEqual(session.title, "My Custom Chat")

    def test_chat_session_str(self):
        """Test the string representation of ChatSession."""
        session = ChatSession.objects.create(user=self.user, title="Test Session Title")

        self.assertEqual(str(session), "Test Session Title")

    def test_chat_session_ordering(self):
        """Test that ChatSessions are ordered by updated_at descending."""
        session1 = ChatSession.objects.create(user=self.user, title="First")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        session2 = ChatSession.objects.create(user=self.user, title="Second")

        sessions = ChatSession.objects.filter(user=self.user)

        # Most recently updated should be first
        self.assertEqual(sessions[0], session2)
        self.assertEqual(sessions[1], session1)

    def test_chat_session_cascade_delete_on_user_delete(self):
        """Test that ChatSessions are deleted when user is deleted."""
        session = ChatSession.objects.create(user=self.user, title="Test")
        session_id = session.id

        self.user.delete()

        self.assertFalse(ChatSession.objects.filter(id=session_id).exists())

    def test_chat_session_title_max_length(self):
        """Test that ChatSession title respects max_length."""
        long_title = "x" * 200  # Exactly at limit
        session = ChatSession.objects.create(user=self.user, title=long_title)

        self.assertEqual(len(session.title), 200)

    def test_chat_session_updated_at_changes(self):
        """Test that updated_at changes when session is saved."""
        session = ChatSession.objects.create(user=self.user, title="Original")
        original_updated_at = session.updated_at

        time.sleep(0.01)
        session.title = "Modified"
        session.save()

        session.refresh_from_db()
        self.assertGreater(session.updated_at, original_updated_at)


class MessageModelTest(TestCase):
    """Test cases for the Message model."""

    def setUp(self):
        """Set up test data for Message tests."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = ChatSession.objects.create(user=self.user, title="Test Session")

    def test_create_user_message(self):
        """Test creating a user message."""
        message = Message.objects.create(
            session=self.session, role="user", content="Hello, AI!"
        )

        self.assertEqual(message.session, self.session)
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello, AI!")
        self.assertIsNone(message.model_used)
        self.assertIsNotNone(message.created_at)

    def test_create_assistant_message(self):
        """Test creating an assistant message with model_used."""
        message = Message.objects.create(
            session=self.session,
            role="assistant",
            content="Hello! How can I help?",
            model_used="gemini-2.5-flash",
        )

        self.assertEqual(message.role, "assistant")
        self.assertEqual(message.model_used, "gemini-2.5-flash")

    def test_message_ordering(self):
        """Test that messages are ordered by created_at ascending."""
        msg1 = Message.objects.create(
            session=self.session, role="user", content="First message"
        )
        time.sleep(0.01)
        msg2 = Message.objects.create(
            session=self.session, role="assistant", content="Second message"
        )

        messages = Message.objects.filter(session=self.session)

        # Oldest first (chronological order)
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)

    def test_message_cascade_delete_on_session_delete(self):
        """Test that Messages are deleted when session is deleted."""
        message = Message.objects.create(
            session=self.session, role="user", content="Test message"
        )
        message_id = message.id

        self.session.delete()

        self.assertFalse(Message.objects.filter(id=message_id).exists())

    def test_message_get_html_content_plain_text(self):
        """Test get_html_content with plain text."""
        message = Message.objects.create(
            session=self.session, role="assistant", content="Hello, world!"
        )

        html = message.get_html_content()

        self.assertIn("Hello, world!", html)
        self.assertIn("<p>", html)

    def test_message_get_html_content_bold(self):
        """Test get_html_content with bold markdown."""
        message = Message.objects.create(
            session=self.session, role="assistant", content="This is **bold** text."
        )

        html = message.get_html_content()

        self.assertIn("<strong>bold</strong>", html)

    def test_message_get_html_content_code_block(self):
        """Test get_html_content with fenced code block."""
        message = Message.objects.create(
            session=self.session,
            role="assistant",
            content='```python\nprint("hello")\n```',
        )

        html = message.get_html_content()

        self.assertIn("print", html)
        self.assertIn("hello", html)

    def test_message_get_html_content_empty(self):
        """Test get_html_content with empty content."""
        message = Message.objects.create(
            session=self.session, role="assistant", content=""
        )

        html = message.get_html_content()

        self.assertEqual(html, "")

    def test_message_get_html_content_list(self):
        """Test get_html_content with markdown list."""
        message = Message.objects.create(
            session=self.session,
            role="assistant",
            content="- Item 1\n- Item 2\n- Item 3",
        )

        html = message.get_html_content()

        self.assertIn("<li>", html)
        self.assertIn("Item 1", html)

    def test_message_role_choices(self):
        """Test that message role choices are valid."""
        valid_roles = ["user", "assistant"]

        for role in valid_roles:
            message = Message.objects.create(
                session=self.session, role=role, content=f"{role} message"
            )
            self.assertEqual(message.role, role)


class DocumentModelTest(TestCase):
    """Test cases for the Document model."""

    def setUp(self):
        """Set up test data for Document tests."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = ChatSession.objects.create(user=self.user, title="Test Session")

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.cloudinary")
    def test_create_document(self, mock_cloudinary):
        """Test creating a Document."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}

        # Create a simple test file
        test_file = SimpleUploadedFile(
            name="test.pdf",
            content=b"%PDF-1.4 fake pdf content",
            content_type="application/pdf",
        )

        document = Document.objects.create(
            session=self.session, file=test_file, title="Test Document"
        )

        self.assertEqual(document.session, self.session)
        self.assertEqual(document.title, "Test Document")
        self.assertIsNotNone(document.uploaded_at)
        self.assertTrue(document.file.name.endswith(".pdf"))

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.cloudinary")
    def test_document_str(self, mock_cloudinary):
        """Test the string representation of Document."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}

        test_file = SimpleUploadedFile(
            name="test.pdf",
            content=b"%PDF-1.4 fake pdf content",
            content_type="application/pdf",
        )

        document = Document.objects.create(
            session=self.session, file=test_file, title="My Test Document"
        )

        self.assertEqual(str(document), "My Test Document")

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.cloudinary")
    def test_document_ordering(self, mock_cloudinary):
        """Test that Documents are ordered by uploaded_at descending."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}

        file1 = SimpleUploadedFile("test1.pdf", b"content1", "application/pdf")
        doc1 = Document.objects.create(
            session=self.session, file=file1, title="First Doc"
        )

        time.sleep(0.01)

        file2 = SimpleUploadedFile("test2.pdf", b"content2", "application/pdf")
        doc2 = Document.objects.create(
            session=self.session, file=file2, title="Second Doc"
        )

        docs = Document.objects.filter(session=self.session)

        # Most recently uploaded should be first
        self.assertEqual(docs[0], doc2)
        self.assertEqual(docs[1], doc1)

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.delete_session_vectors")
    @patch("chat.signals.cloudinary")
    def test_document_cascade_delete_on_session_delete(
        self, mock_cloudinary, mock_delete_vectors
    ):
        """Test that Documents are deleted when session is deleted."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}
        mock_delete_vectors.return_value = True

        test_file = SimpleUploadedFile("test.pdf", b"content", "application/pdf")
        document = Document.objects.create(
            session=self.session, file=test_file, title="Test Doc"
        )
        doc_id = document.id

        self.session.delete()

        self.assertFalse(Document.objects.filter(id=doc_id).exists())

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.cloudinary")
    def test_document_session_relationship(self, mock_cloudinary):
        """Test accessing documents through session relationship."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}

        file1 = SimpleUploadedFile("doc1.pdf", b"content1", "application/pdf")
        file2 = SimpleUploadedFile("doc2.pdf", b"content2", "application/pdf")

        Document.objects.create(session=self.session, file=file1, title="Doc 1")
        Document.objects.create(session=self.session, file=file2, title="Doc 2")

        # Access through reverse relationship
        self.assertEqual(self.session.documents.count(), 2)


class ModelRelationshipTest(TestCase):
    """Test relationships between models."""

    def setUp(self):
        """Set up test data for relationship tests."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_user_has_multiple_sessions(self):
        """Test that a user can have multiple chat sessions."""
        session1 = ChatSession.objects.create(user=self.user, title="Chat 1")
        session2 = ChatSession.objects.create(user=self.user, title="Chat 2")
        session3 = ChatSession.objects.create(user=self.user, title="Chat 3")

        user_sessions = ChatSession.objects.filter(user=self.user)

        self.assertEqual(user_sessions.count(), 3)

    def test_session_has_multiple_messages(self):
        """Test that a session can have multiple messages."""
        session = ChatSession.objects.create(user=self.user, title="Test")

        Message.objects.create(session=session, role="user", content="Q1")
        Message.objects.create(session=session, role="assistant", content="A1")
        Message.objects.create(session=session, role="user", content="Q2")
        Message.objects.create(session=session, role="assistant", content="A2")

        self.assertEqual(session.messages.count(), 4)

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.cloudinary")
    def test_session_has_multiple_documents(self, mock_cloudinary):
        """Test that a session can have multiple documents."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}

        session = ChatSession.objects.create(user=self.user, title="Test")

        for i in range(3):
            test_file = SimpleUploadedFile(f"doc{i}.pdf", b"content", "application/pdf")
            Document.objects.create(session=session, file=test_file, title=f"Doc {i}")

        self.assertEqual(session.documents.count(), 3)

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.delete_session_vectors")
    @patch("chat.signals.cloudinary")
    def test_cascade_delete_user_removes_all_related(
        self, mock_cloudinary, mock_delete_vectors
    ):
        """Test that deleting user removes sessions, messages, and documents."""
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}
        mock_delete_vectors.return_value = True

        session = ChatSession.objects.create(user=self.user, title="Test")
        Message.objects.create(session=session, role="user", content="Test")

        test_file = SimpleUploadedFile("doc.pdf", b"content", "application/pdf")
        Document.objects.create(session=session, file=test_file, title="Doc")

        session_id = session.id

        # Delete user
        self.user.delete()

        # Verify cascade
        self.assertEqual(ChatSession.objects.filter(id=session_id).count(), 0)
        self.assertEqual(Message.objects.filter(session_id=session_id).count(), 0)
        self.assertEqual(Document.objects.filter(session_id=session_id).count(), 0)

    def test_different_users_sessions_isolated(self):
        """Test that different users' sessions are isolated."""
        user2 = User.objects.create_user(username="user2", password="pass123")

        ChatSession.objects.create(user=self.user, title="User1 Chat")
        ChatSession.objects.create(user=user2, title="User2 Chat")

        user1_sessions = ChatSession.objects.filter(user=self.user)
        user2_sessions = ChatSession.objects.filter(user=user2)

        self.assertEqual(user1_sessions.count(), 1)
        self.assertEqual(user2_sessions.count(), 1)
        self.assertNotEqual(user1_sessions[0].id, user2_sessions[0].id)

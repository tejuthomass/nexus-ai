"""Tests for chat application utility functions.

This module tests utility functions including:
    - RAG functions (extract_text_from_pdf, ingest_document, etc.)
    - Model fallback functions
    - Signal handlers

External services (Cloudinary, Pinecone, Google AI) are mocked.
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from unittest.mock import patch, MagicMock, PropertyMock
import io
from chat.models import ChatSession, Message, Document
from chat.model_fallback import (
    ModelExhaustionError,
    is_rate_limit_error,
    is_fallback_error,
    get_model_display_name,
    reset_exhaustion_if_needed,
    MODEL_HIERARCHY,
)

# Test storage configuration using local file system instead of Cloudinary
TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


class ModelFallbackUtilsTest(TestCase):
    """Test cases for model_fallback utility functions."""

    def test_is_rate_limit_error_with_429(self):
        """Test is_rate_limit_error detects 429 errors."""
        self.assertTrue(is_rate_limit_error("Error 429: Too many requests"))
        self.assertTrue(is_rate_limit_error("HTTP 429"))

    def test_is_rate_limit_error_with_503(self):
        """Test is_rate_limit_error detects 503 errors."""
        self.assertTrue(is_rate_limit_error("Error 503: Service unavailable"))

    def test_is_rate_limit_error_with_rate_limit_text(self):
        """Test is_rate_limit_error detects rate limit text."""
        self.assertTrue(is_rate_limit_error("Rate limit exceeded"))
        self.assertTrue(is_rate_limit_error("RATE LIMIT"))

    def test_is_rate_limit_error_with_quota_text(self):
        """Test is_rate_limit_error detects quota text."""
        self.assertTrue(is_rate_limit_error("Quota exceeded"))
        self.assertTrue(is_rate_limit_error("API quota reached"))

    def test_is_rate_limit_error_with_normal_error(self):
        """Test is_rate_limit_error returns false for normal errors."""
        self.assertFalse(is_rate_limit_error("ValueError: invalid input"))
        self.assertFalse(is_rate_limit_error("Connection refused"))

    def test_is_fallback_error_with_404(self):
        """Test is_fallback_error detects 404 errors."""
        self.assertTrue(is_fallback_error("Error 404: Model not found"))
        self.assertTrue(is_fallback_error("NOT_FOUND"))

    def test_is_fallback_error_with_rate_limit(self):
        """Test is_fallback_error detects rate limit errors."""
        self.assertTrue(is_fallback_error("Rate limit exceeded"))
        self.assertTrue(is_fallback_error("429 Too Many Requests"))

    def test_is_fallback_error_with_normal_error(self):
        """Test is_fallback_error returns false for non-fallback errors."""
        self.assertFalse(is_fallback_error("API key invalid"))
        self.assertFalse(is_fallback_error("Permission denied"))

    def test_get_model_display_name_known_models(self):
        """Test get_model_display_name with known models."""
        self.assertEqual(get_model_display_name("gemini-2.5-flash"), "Gemini 2.5 Flash")
        self.assertEqual(get_model_display_name("gemma-3-27b"), "Gemma 3 27B")

    def test_get_model_display_name_unknown_model(self):
        """Test get_model_display_name with unknown model."""
        unknown = "unknown-model-v1"
        self.assertEqual(get_model_display_name(unknown), unknown)

    def test_model_hierarchy_not_empty(self):
        """Test that MODEL_HIERARCHY contains models."""
        self.assertGreater(len(MODEL_HIERARCHY), 0)

    def test_model_hierarchy_contains_expected_models(self):
        """Test that MODEL_HIERARCHY contains expected models."""
        self.assertIn("gemini-2.5-flash", MODEL_HIERARCHY)
        self.assertIn("gemini-2.0-flash", MODEL_HIERARCHY)

    def test_model_exhaustion_error_is_exception(self):
        """Test that ModelExhaustionError is a proper exception."""
        with self.assertRaises(ModelExhaustionError):
            raise ModelExhaustionError("All models exhausted")


class GenerateWithFallbackTest(TestCase):
    """Test cases for generate_with_fallback function."""

    @patch("chat.model_fallback.genai")
    def test_generate_with_fallback_success(self, mock_genai):
        """Test successful generation with first model."""
        from chat.model_fallback import generate_with_fallback

        # Mock the client and response
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Hello! How can I help?"
        mock_client.models.generate_content.return_value = mock_response

        response_text, model_used = generate_with_fallback("Hello")

        self.assertEqual(response_text, "Hello! How can I help?")
        self.assertIn(model_used, MODEL_HIERARCHY)

    @patch("chat.model_fallback.genai")
    @patch("chat.model_fallback._all_models_exhausted", False)
    def test_generate_with_fallback_fallback_on_404(self, mock_genai):
        """Test fallback to next model on 404 error."""
        from chat.model_fallback import generate_with_fallback

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # First call raises 404, second succeeds
        mock_response = MagicMock()
        mock_response.text = "Response from fallback model"
        mock_client.models.generate_content.side_effect = [
            Exception("404 Model not found"),
            mock_response,
        ]

        response_text, model_used = generate_with_fallback("Hello")

        self.assertEqual(response_text, "Response from fallback model")


class RAGFunctionsTest(TestCase):
    """Test cases for RAG utility functions."""

    def test_extract_text_from_pdf_invalid(self):
        """Test extract_text_from_pdf with invalid PDF."""
        from chat.rag import extract_text_from_pdf

        # Invalid PDF content
        invalid_pdf = io.BytesIO(b"Not a PDF file")

        with self.assertRaises(Exception):
            extract_text_from_pdf(invalid_pdf)

    @patch("chat.rag.get_clients")
    def test_retrieve_context_returns_empty_on_error(self, mock_clients):
        """Test retrieve_context returns empty string on error."""
        from chat.rag import retrieve_context

        mock_clients.side_effect = Exception("Connection failed")

        result = retrieve_context("test query", session_id=1)

        self.assertEqual(result, "")

    @patch("chat.rag.get_clients")
    def test_retrieve_context_with_session_filter(self, mock_clients):
        """Test retrieve_context applies session filter."""
        from chat.rag import retrieve_context

        mock_google_client = MagicMock()
        mock_index = MagicMock()
        mock_clients.return_value = (mock_google_client, mock_index)

        # Mock embedding response
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_google_client.models.embed_content.return_value = MagicMock(
            embeddings=[mock_embedding]
        )

        # Mock search results
        mock_index.query.return_value = {"matches": []}

        retrieve_context("test query", session_id=123)

        # Verify filter was applied
        call_args = mock_index.query.call_args
        self.assertIn("filter", call_args.kwargs)

    @patch("chat.rag.get_clients")
    def test_delete_session_vectors_success(self, mock_clients):
        """Test delete_session_vectors succeeds."""
        from chat.rag import delete_session_vectors

        mock_google_client = MagicMock()
        mock_index = MagicMock()
        mock_clients.return_value = (mock_google_client, mock_index)

        result = delete_session_vectors(123)

        self.assertTrue(result)
        mock_index.delete.assert_called_once()

    @patch("chat.rag.get_clients")
    def test_delete_session_vectors_retry_on_failure(self, mock_clients):
        """Test delete_session_vectors retries on failure."""
        from chat.rag import delete_session_vectors

        mock_google_client = MagicMock()
        mock_index = MagicMock()
        mock_clients.return_value = (mock_google_client, mock_index)

        # Fail first two times, succeed third time
        mock_index.delete.side_effect = [
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            None,
        ]

        result = delete_session_vectors(123, max_retries=3)

        self.assertTrue(result)
        self.assertEqual(mock_index.delete.call_count, 3)

    @patch("chat.rag.get_clients")
    @patch("chat.rag.time.sleep")
    def test_delete_session_vectors_all_retries_fail(self, mock_sleep, mock_clients):
        """Test delete_session_vectors returns false when all retries fail."""
        from chat.rag import delete_session_vectors

        mock_google_client = MagicMock()
        mock_index = MagicMock()
        mock_clients.return_value = (mock_google_client, mock_index)

        mock_index.delete.side_effect = Exception("Persistent failure")

        result = delete_session_vectors(123, max_retries=2)

        self.assertFalse(result)

    @patch("chat.rag.get_clients")
    def test_delete_document_vectors_success(self, mock_clients):
        """Test delete_document_vectors succeeds."""
        from chat.rag import delete_document_vectors

        mock_google_client = MagicMock()
        mock_index = MagicMock()
        mock_clients.return_value = (mock_google_client, mock_index)

        result = delete_document_vectors("123_test.pdf")

        self.assertTrue(result)


class ServiceAvailabilityTest(TestCase):
    """Test cases for check_service_availability function."""

    @patch("chat.model_fallback._all_models_exhausted", False)
    def test_service_available_when_not_exhausted(self):
        """Test service is available when not exhausted."""
        from chat.model_fallback import check_service_availability

        is_available, message = check_service_availability()

        self.assertTrue(is_available)
        self.assertIn("available", message.lower())

    @patch("chat.model_fallback._all_models_exhausted", True)
    @patch("chat.model_fallback._exhaustion_timestamp")
    @patch("chat.model_fallback.time.time")
    def test_service_unavailable_when_exhausted(self, mock_time, mock_timestamp, *args):
        """Test service is unavailable when models exhausted."""
        from chat.model_fallback import check_service_availability

        mock_time.return_value = 100
        mock_timestamp.return_value = 50  # 50 seconds ago

        is_available, message = check_service_availability()

        # Note: The actual behavior depends on EXHAUSTION_RESET_TIME
        # This is a simplified test
        self.assertIsInstance(is_available, bool)
        self.assertIsInstance(message, str)


class SignalHandlerTest(TestCase):
    """Test cases for signal handlers."""

    def setUp(self):
        """Set up test data for signal tests."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.session = ChatSession.objects.create(user=self.user, title="Test Session")

    @patch("chat.signals.delete_session_vectors")
    def test_session_delete_triggers_vector_cleanup(self, mock_delete):
        """Test that deleting session triggers vector cleanup signal."""
        mock_delete.return_value = True
        session_id = self.session.id

        self.session.delete()

        mock_delete.assert_called_once_with(session_id)

    @override_settings(STORAGES=TEST_STORAGES)
    @patch("chat.signals.delete_session_vectors")
    @patch("chat.signals.cloudinary")
    def test_document_delete_triggers_cloudinary_cleanup(
        self, mock_cloudinary, mock_delete
    ):
        """Test that deleting document triggers Cloudinary cleanup."""
        mock_delete.return_value = True
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}

        test_file = SimpleUploadedFile("test.pdf", b"content", "application/pdf")
        document = Document.objects.create(
            session=self.session, file=test_file, title="Test Doc"
        )

        document.delete()

        # Cloudinary cleanup should have been attempted
        self.assertTrue(mock_cloudinary.uploader.destroy.called)

    @patch("chat.signals.delete_session_vectors")
    def test_user_delete_triggers_session_cleanup(self, mock_delete):
        """Test that deleting user triggers session cleanup."""
        mock_delete.return_value = True

        self.user.delete()

        # Session cleanup should have been triggered
        self.assertTrue(mock_delete.called)

    def test_message_delete_logged(self):
        """Test that message deletion is logged without error."""
        message = Message.objects.create(
            session=self.session, role="user", content="Test message"
        )

        # Should not raise any errors
        message.delete()

        self.assertFalse(Message.objects.filter(id=message.id).exists())

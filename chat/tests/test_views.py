"""Tests for chat application views.

This module tests all view functions and API endpoints including:
    - Main chat interface (chat_view)
    - Session management (new_chat, rename_chat, delete)
    - Admin dashboard and user management
    - API endpoints
    - Authentication and authorization
    - HTMX partial responses

External services (Cloudinary, Pinecone, Google AI) are mocked.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from chat.models import ChatSession, Message, Document


class ChatViewTest(TestCase):
    """Test cases for the main chat_view function."""

    def setUp(self):
        """Set up test data for chat view tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.session = ChatSession.objects.create(user=self.user, title="Test Session")

    def test_chat_view_requires_login(self):
        """Test that chat view requires authentication."""
        response = self.client.get(reverse("chat"))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_chat_view_authenticated_user(self):
        """Test that authenticated user can access chat view."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("chat"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/index.html")

    def test_chat_view_creates_session_if_none(self):
        """Test that chat view creates a session if user has none."""
        # Delete existing session
        self.session.delete()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("chat"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatSession.objects.filter(user=self.user).count(), 1)

    def test_chat_view_specific_session(self):
        """Test accessing a specific chat session."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("chat_session", args=[self.session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.session.title)

    def test_chat_view_404_for_other_users_session(self):
        """Test that user cannot access another user's session."""
        other_user = User.objects.create_user(username="other", password="pass123")
        other_session = ChatSession.objects.create(
            user=other_user, title="Other's Session"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("chat_session", args=[other_session.id]))

        self.assertEqual(response.status_code, 404)

    def test_chat_view_htmx_title_partial(self):
        """Test HTMX partial response for title update."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("chat_session", args=[self.session.id]),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="title",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/partials/chat_title.html")

    def test_chat_view_htmx_sidebar_partial(self):
        """Test HTMX partial response for sidebar update."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("chat_session", args=[self.session.id]),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="sidebar",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/partials/sidebar_list.html")

    def test_chat_view_displays_messages(self):
        """Test that chat view displays session messages."""
        Message.objects.create(
            session=self.session, role="user", content="Hello there!"
        )
        Message.objects.create(
            session=self.session, role="assistant", content="Hi! How can I help?"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("chat_session", args=[self.session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello there!")

    @patch("chat.views.generate_with_fallback")
    @patch("chat.views.retrieve_context")
    def test_chat_view_post_message(self, mock_retrieve, mock_generate):
        """Test posting a message to chat view."""
        mock_generate.return_value = ("Hello! How can I help?", "gemini-2.5-flash")
        mock_retrieve.return_value = ""

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("chat_session", args=[self.session.id]), {"message": "Hello AI!"}
        )

        self.assertEqual(response.status_code, 200)
        # Check message was created
        self.assertEqual(Message.objects.filter(session=self.session).count(), 2)

    def test_chat_view_post_empty_message(self):
        """Test posting an empty message returns error."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("chat_session", args=[self.session.id]), {"message": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/partials/system_message.html")

    def test_chat_view_post_message_too_long(self):
        """Test posting a message that's too long."""
        self.client.login(username="testuser", password="testpass123")

        long_message = "x" * 5001  # Exceeds 5000 char limit
        response = self.client.post(
            reverse("chat_session", args=[self.session.id]), {"message": long_message}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "too long")


class NewChatViewTest(TestCase):
    """Test cases for the new_chat view function."""

    def setUp(self):
        """Set up test data for new chat tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_new_chat_requires_login(self):
        """Test that new_chat requires authentication."""
        response = self.client.get(reverse("new_chat"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_new_chat_creates_session(self):
        """Test that new_chat creates a new session."""
        # Create an initial session with messages
        session = ChatSession.objects.create(user=self.user, title="Old Chat")
        Message.objects.create(session=session, role="user", content="Hello")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("new_chat"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChatSession.objects.filter(user=self.user).count(), 2)

    def test_new_chat_reuses_empty_session(self):
        """Test that new_chat reuses existing empty session."""
        # Create an empty session
        session = ChatSession.objects.create(user=self.user, title="Empty Chat")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("new_chat"))

        self.assertEqual(response.status_code, 302)
        # Should not create a new session
        self.assertEqual(ChatSession.objects.filter(user=self.user).count(), 1)


class RenameChatViewTest(TestCase):
    """Test cases for the rename_chat view function."""

    def setUp(self):
        """Set up test data for rename chat tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.session = ChatSession.objects.create(
            user=self.user, title="Original Title"
        )
        # Add a message so it's not empty
        Message.objects.create(session=self.session, role="user", content="Hello")

    def test_rename_chat_requires_login(self):
        """Test that rename_chat requires authentication."""
        response = self.client.post(
            reverse("rename_chat", args=[self.session.id]), {"new_title": "New Title"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_rename_chat_success(self):
        """Test successfully renaming a chat."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("rename_chat", args=[self.session.id]), {"new_title": "New Title"}
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.title, "New Title")

    def test_rename_chat_strips_whitespace(self):
        """Test that rename_chat strips whitespace from title."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("rename_chat", args=[self.session.id]),
            {"new_title": "  Trimmed Title  "},
        )

        self.session.refresh_from_db()
        self.assertEqual(self.session.title, "Trimmed Title")

    def test_rename_chat_404_for_other_users_session(self):
        """Test that user cannot rename another user's session."""
        other_user = User.objects.create_user(username="other", password="pass123")
        other_session = ChatSession.objects.create(
            user=other_user, title="Other's Session"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("rename_chat", args=[other_session.id]),
            {"new_title": "Hacked Title"},
        )

        self.assertEqual(response.status_code, 404)

    def test_rename_empty_session_returns_204(self):
        """Test that renaming empty session returns 204."""
        empty_session = ChatSession.objects.create(
            user=self.user, title="Empty Session"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("rename_chat", args=[empty_session.id]), {"new_title": "New Title"}
        )

        self.assertEqual(response.status_code, 204)


class DeleteUserChatSessionViewTest(TestCase):
    """Test cases for the delete_user_chat_session view function."""

    def setUp(self):
        """Set up test data for delete session tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.session = ChatSession.objects.create(user=self.user, title="Test Session")
        Message.objects.create(session=self.session, role="user", content="Hello")

    @patch("chat.signals.delete_session_vectors")
    def test_delete_session_requires_login(self, mock_delete):
        """Test that delete requires authentication."""
        mock_delete.return_value = True

        response = self.client.post(
            reverse("delete_user_chat_session", args=[self.session.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    @patch("chat.signals.delete_session_vectors")
    def test_delete_own_session(self, mock_delete):
        """Test deleting own session."""
        mock_delete.return_value = True
        session_id = self.session.id

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("delete_user_chat_session", args=[session_id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ChatSession.objects.filter(id=session_id).exists())

    @patch("chat.signals.delete_session_vectors")
    def test_delete_other_users_session_404(self, mock_delete):
        """Test that user cannot delete another user's session."""
        mock_delete.return_value = True
        other_user = User.objects.create_user(username="other", password="pass123")
        other_session = ChatSession.objects.create(
            user=other_user, title="Other's Session"
        )
        Message.objects.create(session=other_session, role="user", content="Hello")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("delete_user_chat_session", args=[other_session.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_delete_empty_session_returns_204(self):
        """Test that deleting empty session returns 204."""
        empty_session = ChatSession.objects.create(
            user=self.user, title="Empty Session"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("delete_user_chat_session", args=[empty_session.id])
        )

        self.assertEqual(response.status_code, 204)

    @patch("chat.signals.delete_session_vectors")
    def test_delete_with_htmx_returns_redirect_header(self, mock_delete):
        """Test that HTMX request returns redirect header."""
        mock_delete.return_value = True
        session_id = self.session.id

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("delete_user_chat_session", args=[session_id]),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Redirect"), "/")


class AdminDashboardViewTest(TestCase):
    """Test cases for the admin_dashboard view function."""

    def setUp(self):
        """Set up test data for admin dashboard tests."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="userpass123"
        )

    def test_dashboard_requires_staff(self):
        """Test that dashboard requires staff status."""
        self.client.login(username="regular", password="userpass123")

        response = self.client.get(reverse("dashboard"))

        # Should redirect to admin login
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_by_admin(self):
        """Test that admin can access dashboard."""
        self.client.login(username="admin", password="adminpass123")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/dashboard.html")

    def test_dashboard_shows_users(self):
        """Test that dashboard shows non-superuser accounts."""
        self.client.login(username="admin", password="adminpass123")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "regular")


class AdminDeleteUserViewTest(TestCase):
    """Test cases for the delete_user admin view function."""

    def setUp(self):
        """Set up test data for admin delete user tests."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="userpass123"
        )

    def test_delete_user_requires_staff(self):
        """Test that delete_user requires staff status."""
        self.client.login(username="regular", password="userpass123")

        response = self.client.post(reverse("delete_user", args=[self.regular_user.id]))

        self.assertEqual(response.status_code, 302)

    @patch("chat.signals.delete_session_vectors")
    def test_admin_can_delete_user(self, mock_delete):
        """Test that admin can delete a user."""
        mock_delete.return_value = True
        user_id = self.regular_user.id

        self.client.login(username="admin", password="adminpass123")
        response = self.client.post(reverse("delete_user", args=[user_id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=user_id).exists())


class AdminDeleteSessionViewTest(TestCase):
    """Test cases for the delete_chat_session admin view function."""

    def setUp(self):
        """Set up test data for admin delete session tests."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="userpass123"
        )
        self.session = ChatSession.objects.create(
            user=self.regular_user, title="User's Session"
        )

    def test_delete_session_requires_staff(self):
        """Test that delete_chat_session requires staff status."""
        self.client.login(username="regular", password="userpass123")

        response = self.client.post(
            reverse("delete_chat_session", args=[self.session.id])
        )

        self.assertEqual(response.status_code, 302)

    @patch("chat.signals.delete_session_vectors")
    def test_admin_can_delete_any_session(self, mock_delete):
        """Test that admin can delete any user's session."""
        mock_delete.return_value = True
        session_id = self.session.id

        self.client.login(username="admin", password="adminpass123")
        response = self.client.post(reverse("delete_chat_session", args=[session_id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ChatSession.objects.filter(id=session_id).exists())


class ViewChatReadonlyViewTest(TestCase):
    """Test cases for the view_chat_readonly admin view function."""

    def setUp(self):
        """Set up test data for readonly view tests."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="userpass123"
        )
        self.session = ChatSession.objects.create(
            user=self.regular_user, title="User's Session"
        )
        Message.objects.create(session=self.session, role="user", content="Hello!")

    def test_readonly_view_requires_staff(self):
        """Test that view_chat_readonly requires staff status."""
        self.client.login(username="regular", password="userpass123")

        response = self.client.get(
            reverse("view_chat_readonly", args=[self.session.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_can_view_readonly(self):
        """Test that admin can view session in readonly mode."""
        self.client.login(username="admin", password="adminpass123")

        response = self.client.get(
            reverse("view_chat_readonly", args=[self.session.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello!")


class ApiAdminChatViewTest(TestCase):
    """Test cases for the api_admin_chat endpoint."""

    def setUp(self):
        """Set up test data for API tests."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="userpass123"
        )
        self.session = ChatSession.objects.create(
            user=self.regular_user, title="API Test Session"
        )
        Message.objects.create(
            session=self.session, role="user", content="Test message"
        )

    def test_api_requires_staff(self):
        """Test that API endpoint requires staff status."""
        self.client.login(username="regular", password="userpass123")

        response = self.client.get(reverse("api_admin_chat", args=[self.session.id]))

        self.assertEqual(response.status_code, 302)

    def test_api_returns_json(self):
        """Test that API returns JSON response."""
        self.client.login(username="admin", password="adminpass123")

        response = self.client.get(reverse("api_admin_chat", args=[self.session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_returns_session_data(self):
        """Test that API returns correct session data."""
        self.client.login(username="admin", password="adminpass123")

        response = self.client.get(reverse("api_admin_chat", args=[self.session.id]))

        data = response.json()
        self.assertEqual(data["id"], self.session.id)
        self.assertEqual(data["title"], "API Test Session")
        self.assertEqual(data["user"], "regular")
        self.assertEqual(len(data["messages"]), 1)


class CheckAvailabilityViewTest(TestCase):
    """Test cases for the check_availability endpoint."""

    def setUp(self):
        """Set up test data for availability tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_availability_requires_login(self):
        """Test that check_availability requires authentication."""
        response = self.client.get(reverse("check_availability"))

        self.assertEqual(response.status_code, 302)

    @patch("chat.views.check_service_availability")
    def test_availability_returns_json(self, mock_check):
        """Test that endpoint returns JSON response."""
        mock_check.return_value = (True, "Service available")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("check_availability"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    @patch("chat.views.check_service_availability")
    def test_availability_when_available(self, mock_check):
        """Test response when service is available."""
        mock_check.return_value = (True, "Service available")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("check_availability"))

        data = response.json()
        self.assertTrue(data["available"])
        self.assertEqual(data["message"], "Service available")

    @patch("chat.views.check_service_availability")
    def test_availability_when_unavailable(self, mock_check):
        """Test response when service is unavailable."""
        mock_check.return_value = (False, "Service temporarily unavailable")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("check_availability"))

        data = response.json()
        self.assertFalse(data["available"])


class FileUploadViewTest(TestCase):
    """Test cases for file upload functionality in chat_view."""

    def setUp(self):
        """Set up test data for file upload tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.session = ChatSession.objects.create(
            user=self.user, title="Upload Test Session"
        )

    def test_upload_requires_login(self):
        """Test that file upload requires authentication."""
        test_file = SimpleUploadedFile("test.pdf", b"content", "application/pdf")

        response = self.client.post(
            reverse("chat_session", args=[self.session.id]), {"pdf_file": test_file}
        )

        self.assertEqual(response.status_code, 302)

    def test_upload_invalid_extension(self):
        """Test uploading file with invalid extension."""
        self.client.login(username="testuser", password="testpass123")

        test_file = SimpleUploadedFile("test.txt", b"content", "text/plain")

        response = self.client.post(
            reverse("chat_session", args=[self.session.id]), {"pdf_file": test_file}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid file type")

    def test_upload_file_too_large(self):
        """Test uploading file that's too large."""
        self.client.login(username="testuser", password="testpass123")

        # Create file larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)
        test_file = SimpleUploadedFile("large.pdf", large_content, "application/pdf")

        response = self.client.post(
            reverse("chat_session", args=[self.session.id]), {"pdf_file": test_file}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "too large")

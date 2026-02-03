"""Tests for chat application middleware.

This module tests the rate limiting middleware classes:
    - RateLimitMiddleware: General request rate limiting
    - APIRateLimitMiddleware: AI API-specific rate limiting

Middleware tests focus on:
    - Request filtering (which requests are rate limited)
    - Rate limit enforcement
    - Cache interaction
    - Response handling
"""

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from chat.middleware import (
    RateLimitMiddleware,
    APIRateLimitMiddleware,
    USER_REQUESTS_PER_MINUTE,
    USER_REQUESTS_PER_HOUR,
    GLOBAL_PARALLEL_LIMIT
)


class RateLimitMiddlewareTest(TestCase):
    """Test cases for the RateLimitMiddleware class."""

    def setUp(self):
        """Set up test data for middleware tests."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Create a simple get_response callable
        self.get_response = lambda request: HttpResponse('OK')
        self.middleware = RateLimitMiddleware(self.get_response)

    def test_middleware_passes_unauthenticated_requests(self):
        """Test that unauthenticated requests pass through."""
        request = self.factory.post('/chat/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

    def test_middleware_skips_get_requests(self):
        """Test that GET requests are not rate limited."""
        request = self.factory.get('/chat/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    def test_middleware_skips_static_paths(self):
        """Test that static file paths are not rate limited."""
        request = self.factory.post('/static/css/style.css')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    def test_middleware_skips_admin_paths(self):
        """Test that admin paths are not rate limited."""
        request = self.factory.post('/admin/login/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    def test_middleware_skips_login_paths(self):
        """Test that login paths are not rate limited."""
        request = self.factory.post('/accounts/login/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    @patch('chat.middleware.cache')
    def test_middleware_checks_global_limit(self, mock_cache):
        """Test that middleware checks global parallel limit."""
        mock_cache.get.return_value = GLOBAL_PARALLEL_LIMIT + 1
        
        request = self.factory.post('/chat/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('capacity', response.content.decode())

    @patch('chat.middleware.cache')
    def test_middleware_checks_minute_limit(self, mock_cache):
        """Test that middleware checks per-minute limit."""
        # Global limit OK, but minute limit exceeded
        mock_cache.get.side_effect = lambda key, default=0: (
            0 if 'global' in key else USER_REQUESTS_PER_MINUTE + 1
        )
        
        request = self.factory.post('/chat/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('wait', response.content.decode().lower())

    @patch('chat.middleware.cache')
    def test_middleware_increments_counters(self, mock_cache):
        """Test that middleware increments rate limit counters."""
        mock_cache.get.return_value = 0
        
        request = self.factory.post('/chat/')
        request.user = self.user
        
        response = self.middleware(request)
        
        # Verify cache.set was called to increment counters
        self.assertTrue(mock_cache.set.called)

    @patch('chat.middleware.cache')
    def test_rate_limit_response_includes_retry_after(self, mock_cache):
        """Test that rate limit response includes Retry-After header."""
        mock_cache.get.return_value = USER_REQUESTS_PER_MINUTE + 1
        
        request = self.factory.post('/chat/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)


class APIRateLimitMiddlewareTest(TestCase):
    """Test cases for the APIRateLimitMiddleware class."""

    def setUp(self):
        """Set up test data for API middleware tests."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.get_response = lambda request: HttpResponse('OK')
        self.middleware = APIRateLimitMiddleware(self.get_response)

    def test_middleware_skips_non_chat_paths(self):
        """Test that non-chat paths pass through."""
        request = self.factory.post('/other/', {'message': 'test'})
        request.user = self.user
        request.POST = {'message': 'test'}
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    def test_middleware_skips_requests_without_message(self):
        """Test that requests without message param pass through."""
        request = self.factory.post('/chat/')
        request.user = self.user
        request.POST = {}
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    def test_middleware_skips_get_requests(self):
        """Test that GET requests pass through."""
        request = self.factory.get('/chat/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)

    @patch('chat.middleware.cache')
    def test_middleware_rate_limits_api_calls(self, mock_cache):
        """Test that middleware rate limits API calls."""
        mock_cache.get.return_value = 6  # Over limit of 5
        
        request = self.factory.post('/chat/', {'message': 'test'})
        request.user = self.user
        request.POST = {'message': 'test'}
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 429)

    @patch('chat.middleware.cache')
    def test_middleware_allows_under_limit(self, mock_cache):
        """Test that requests under limit pass through."""
        mock_cache.get.return_value = 3  # Under limit of 5
        
        request = self.factory.post('/chat/', {'message': 'test'})
        request.user = self.user
        request.POST = {'message': 'test'}
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)


class MiddlewareIntegrationTest(TestCase):
    """Integration tests for middleware with actual requests."""

    def setUp(self):
        """Set up test data for integration tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_middleware_allows_normal_get_request(self):
        """Test that normal GET requests are allowed."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/chat/')
        
        # Should not be rate limited
        self.assertNotEqual(response.status_code, 429)

    @patch('chat.middleware.cache')
    def test_middleware_cache_failure_fails_open(self, mock_cache):
        """Test that cache failures don't block users."""
        mock_cache.get.side_effect = Exception('Cache unavailable')
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/chat/')
        
        # Should still work despite cache failure
        self.assertNotEqual(response.status_code, 500)

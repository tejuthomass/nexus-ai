"""Rate Limiting Middleware for the Nexus application.

This module implements user-level and API-level rate limiting to ensure
fair resource distribution and prevent abuse of free-tier API resources.

The middleware supports:
    - 10-20 users total
    - 5-10 parallel users simultaneously
    - Free-tier API constraints (Gemini, Pinecone)
    - DatabaseCache stored in NeonDB for multi-worker support

Classes:
    RateLimitMiddleware: General rate limiting for all POST requests.
    APIRateLimitMiddleware: Additional rate limiting for AI API calls.

Constants:
    USER_REQUESTS_PER_MINUTE: Maximum requests per minute per user.
    USER_REQUESTS_PER_HOUR: Maximum requests per hour per user.
    GLOBAL_PARALLEL_LIMIT: Maximum concurrent requests globally.
"""

import logging
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Rate Limit Configuration
# For 10-20 users with 5-10 parallel users on free tier:
# - Allow 10 requests per minute per user (reasonable for conversation flow)
# - Allow 100 requests per hour per user (prevents abuse)
# - Global limit: 50 parallel requests (handles burst from 10 users)

USER_REQUESTS_PER_MINUTE = 10
USER_REQUESTS_PER_HOUR = 100
GLOBAL_PARALLEL_LIMIT = 50

# Cache key prefixes
CACHE_PREFIX_MINUTE = "rate_limit_minute_"
CACHE_PREFIX_HOUR = "rate_limit_hour_"
CACHE_PREFIX_GLOBAL = "rate_limit_global_active"


class RateLimitMiddleware:
    """Middleware to enforce rate limits on user requests.

    Implements three-tier rate limiting:
        1. Per-user minute limit (prevents rapid-fire requests)
        2. Per-user hour limit (prevents long-term abuse)
        3. Global parallel limit (protects free-tier API quotas)

    The middleware only applies to authenticated POST requests on
    non-exempt paths (excludes static, media, admin, and auth pages).

    Attributes:
        get_response: The next middleware or view in the chain.
    """

    def __init__(self, get_response):
        """Initialize the RateLimitMiddleware.

        Args:
            get_response: The next middleware or view callable in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """Process an incoming request with rate limiting.

        Checks rate limits in order of severity:
            1. Global parallel limit (most critical)
            2. Per-user minute limit
            3. Per-user hour limit

        Args:
            request: The HttpRequest object.

        Returns:
            HttpResponse: Either the normal response or a 429 rate limit
                response if limits are exceeded.
        """
        # Only apply rate limiting to authenticated chat/API endpoints
        # Skip static files, admin panel, and authentication pages
        if not self._should_rate_limit(request):
            return self.get_response(request)

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return self.get_response(request)

        user_id = request.user.id

        # Check rate limits in order of severity
        # 1. Check global parallel limit first (most critical)
        if not self._check_global_limit():
            logger.warning("Global parallel limit exceeded")
            return self._rate_limit_response(
                "System is currently at capacity. Please try again in a moment.",
                retry_after=5,
            )

        # 2. Check per-user minute limit
        if not self._check_user_minute_limit(user_id):
            logger.warning("User %s exceeded minute rate limit", user_id)
            return self._rate_limit_response(
                "Too many requests. Please wait a moment before sending another message.",
                retry_after=10,
            )

        # 3. Check per-user hour limit
        if not self._check_user_hour_limit(user_id):
            logger.warning("User %s exceeded hourly rate limit", user_id)
            return self._rate_limit_response(
                "Hourly limit reached. Please try again later.",
                retry_after=300,  # 5 minutes
            )

        # Increment global counter before processing
        self._increment_global_counter()

        try:
            response = self.get_response(request)
        finally:
            # Decrement global counter after processing
            self._decrement_global_counter()

        return response

    def _should_rate_limit(self, request):
        """Determine if this request should be rate limited.

        Exempts static files, media, admin panel, authentication pages,
        and all GET requests from rate limiting.

        Args:
            request: The HttpRequest object.

        Returns:
            bool: True if the request should be rate limited, False otherwise.
        """
        import os

        path = request.path
        admin_path = f"/{os.getenv('ADMIN_URL_PATH', 'admin/')}"

        # Don't rate limit these paths
        exempt_paths = [
            "/static/",
            "/media/",
            admin_path,
            "/accounts/login/",
            "/accounts/logout/",
            "/favicon.ico",
        ]

        for exempt_path in exempt_paths:
            if path.startswith(exempt_path):
                return False

        # Only rate limit POST requests (actual actions)
        # Allow GET requests for loading pages/chat history
        if request.method != "POST":
            return False

        return True

    def _check_global_limit(self):
        """Check if global parallel request limit is exceeded.

        Returns:
            bool: True if under the limit, False if exceeded.
                Returns True if cache is unavailable to fail open.
        """
        try:
            active_requests = cache.get(CACHE_PREFIX_GLOBAL, 0)
            return active_requests < GLOBAL_PARALLEL_LIMIT
        except Exception as e:
            # If cache is unavailable (e.g., table doesn't exist), allow request
            logger.warning("Cache unavailable in _check_global_limit: %s", e)
            return True

    def _increment_global_counter(self):
        """Increment the global active request counter.

        Increments the counter with a 60-second timeout. Logs errors
        but does not raise exceptions to avoid blocking requests.
        """
        try:
            cache_key = CACHE_PREFIX_GLOBAL
            current = cache.get(cache_key, 0)
            cache.set(cache_key, current + 1, timeout=60)
        except Exception as e:
            logger.error("Failed to increment global counter: %s", e)

    def _decrement_global_counter(self):
        """Decrement the global active request counter.

        Decrements the counter ensuring it doesn't go below zero.
        Logs errors but does not raise exceptions.
        """
        try:
            cache_key = CACHE_PREFIX_GLOBAL
            current = cache.get(cache_key, 0)
            if current > 0:
                cache.set(cache_key, current - 1, timeout=60)
        except Exception as e:
            logger.error("Failed to decrement global counter: %s", e)

    def _check_user_minute_limit(self, user_id):
        """Check and update per-user minute rate limit.

        Args:
            user_id: The ID of the user making the request.

        Returns:
            bool: True if the request is allowed, False if limit exceeded.
                Returns True on cache errors to fail open.
        """
        cache_key = f"{CACHE_PREFIX_MINUTE}{user_id}"

        try:
            current_count = cache.get(cache_key, 0)
            if current_count >= USER_REQUESTS_PER_MINUTE:
                return False
            cache.set(cache_key, current_count + 1, timeout=60)
            return True
        except Exception as e:
            logger.error("Cache error in minute limit: %s", e)
            return True  # Fail open to not block users

    def _check_user_hour_limit(self, user_id):
        """Check and update per-user hourly rate limit.

        Args:
            user_id: The ID of the user making the request.

        Returns:
            bool: True if the request is allowed, False if limit exceeded.
                Returns True on cache errors to fail open.
        """
        cache_key = f"{CACHE_PREFIX_HOUR}{user_id}"

        try:
            current_count = cache.get(cache_key, 0)
            if current_count >= USER_REQUESTS_PER_HOUR:
                return False
            cache.set(cache_key, current_count + 1, timeout=3600)
            return True
        except Exception as e:
            logger.error("Cache error in hour limit: %s", e)
            return True  # Fail open to not block users

    def _rate_limit_response(self, message, retry_after=60):
        """Generate a rate limit response.

        Creates a JSON response with rate limit error details and
        sets the Retry-After header.

        Args:
            message: The user-friendly error message to display.
            retry_after: Seconds until the client should retry.
                Defaults to 60.

        Returns:
            JsonResponse: A 429 status response with error details.
        """
        # Check if this is an HTMX request
        _ = (
            "HX-Request" in self.get_response.__self__.META
            if hasattr(self.get_response, "__self__")
            else False
        )

        # For HTMX requests, return HTML partial
        # For API requests, return JSON
        response = JsonResponse(
            {
                "error": "rate_limit_exceeded",
                "message": message,
                "retry_after": retry_after,
            },
            status=429,
        )

        response["Retry-After"] = str(retry_after)
        return response


class APIRateLimitMiddleware:
    """Additional rate limiting specifically for AI API calls.

    This middleware provides an extra layer of protection for expensive
    AI API operations beyond the general request rate limiting. It limits
    users to 5 AI calls per minute.

    Attributes:
        get_response: The next middleware or view in the chain.
    """

    def __init__(self, get_response):
        """Initialize the APIRateLimitMiddleware.

        Args:
            get_response: The next middleware or view callable in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """Process an incoming request with API-specific rate limiting.

        Only applies to POST requests on chat endpoints that contain
        a message parameter.

        Args:
            request: The HttpRequest object.

        Returns:
            HttpResponse: Either the normal response or a 429 rate limit
                response if the AI API limit is exceeded.
        """
        # Only apply to chat message endpoints
        if (
            request.method == "POST"
            and "/chat/" in request.path
            and request.POST.get("message")
        ):
            if not self._check_api_rate_limit(request.user.id):
                logger.warning("User %s exceeded API rate limit", request.user.id)
                return JsonResponse(
                    {
                        "error": "api_rate_limit",
                        "message": "AI API rate limit reached. Please wait before sending another message.",
                        "retry_after": 30,
                    },
                    status=429,
                )

        return self.get_response(request)

    def _check_api_rate_limit(self, user_id):
        """Check API-specific rate limit for a user.

        More restrictive than general rate limiting, allowing only
        5 AI calls per minute per user.

        Args:
            user_id: The ID of the user making the request.

        Returns:
            bool: True if the request is allowed, False if limit exceeded.
                Returns True on cache errors to fail open.
        """
        cache_key = f"api_rate_limit_{user_id}"

        try:
            current_count = cache.get(cache_key, 0)
            if current_count >= 5:  # 5 AI calls per minute
                return False
            cache.set(cache_key, current_count + 1, timeout=60)
            return True
        except Exception as e:
            logger.error("Cache error in API limit: %s", e)
            return True  # Fail open to not block users

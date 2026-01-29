"""
Rate Limiting Middleware for Nexus AI

Implements user-level rate limiting to ensure fair resource distribution
and prevent abuse of free-tier API resources.

Configuration:
- Supports 10-20 users total
- Handles 5-10 parallel users simultaneously
- Optimized for free-tier API constraints (Gemini, Pinecone)
- Multi-worker safe with Redis atomic operations
"""

import time
import logging
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Rate Limit Configuration
# For 10-20 users with 5-10 parallel users on free tier:
# - Allow 10 requests per minute per user (reasonable for conversation flow)
# - Allow 100 requests per hour per user (prevents abuse)
# - Global limit: 50 parallel requests (handles burst from 10 users)

USER_REQUESTS_PER_MINUTE = 10
USER_REQUESTS_PER_HOUR = 100
GLOBAL_PARALLEL_LIMIT = 50

# Check if using Redis (for multi-worker support)
def _is_redis_cache():
    """Check if Redis cache backend is configured."""
    cache_backend = settings.CACHES['default']['BACKEND']
    return 'redis' in cache_backend.lower()


# Cache key prefixes
CACHE_PREFIX_MINUTE = "rate_limit_minute_"
CACHE_PREFIX_HOUR = "rate_limit_hour_"
CACHE_PREFIX_GLOBAL = "rate_limit_global_active"


class RateLimitMiddleware:
    """
    Middleware to enforce rate limits on user requests.
    
    Implements three-tier rate limiting:
    1. Per-user minute limit (prevents rapid-fire requests)
    2. Per-user hour limit (prevents long-term abuse)
    3. Global parallel limit (protects free-tier API quotas)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
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
            logger.warning(f"Global parallel limit exceeded")
            return self._rate_limit_response(
                "System is currently at capacity. Please try again in a moment.",
                retry_after=5
            )
        
        # 2. Check per-user minute limit
        if not self._check_user_minute_limit(user_id):
            logger.warning(f"User {user_id} exceeded minute rate limit")
            return self._rate_limit_response(
                "Too many requests. Please wait a moment before sending another message.",
                retry_after=10
            )
        
        # 3. Check per-user hour limit
        if not self._check_user_hour_limit(user_id):
            logger.warning(f"User {user_id} exceeded hourly rate limit")
            return self._rate_limit_response(
                "Hourly limit reached. Please try again later.",
                retry_after=300  # 5 minutes
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
        """Determine if this request should be rate limited."""
        import os
        path = request.path
        admin_path = f"/{os.getenv('ADMIN_URL_PATH', 'admin/')}"
        
        # Don't rate limit these paths
        exempt_paths = [
            '/static/',
            '/media/',
            admin_path,
            '/accounts/login/',
            '/accounts/logout/',
            '/favicon.ico',
        ]
        
        for exempt_path in exempt_paths:
            if path.startswith(exempt_path):
                return False
        
        # Only rate limit POST requests (actual actions)
        # Allow GET requests for loading pages/chat history
        if request.method != 'POST':
            return False
        
        return True
    
    def _check_global_limit(self):
        """Check if global parallel request limit is exceeded."""
        active_requests = cache.get(CACHE_PREFIX_GLOBAL, 0)
        return active_requests < GLOBAL_PARALLEL_LIMIT
    
    def _increment_global_counter(self):
        """Increment global active request counter atomically."""
        try:
            cache_key = CACHE_PREFIX_GLOBAL
            if _is_redis_cache():
                # Redis atomic increment
                cache.incr(cache_key)
                cache.expire(cache_key, 60)
            else:
                # Fallback for non-Redis (development)
                current = cache.get(cache_key, 0)
                cache.set(cache_key, current + 1, timeout=60)
        except Exception as e:
            logger.error(f"Failed to increment global counter: {e}")
    
    def _decrement_global_counter(self):
        """Decrement global active request counter atomically."""
        try:
            cache_key = CACHE_PREFIX_GLOBAL
            if _is_redis_cache():
                # Redis atomic decrement
                new_value = cache.decr(cache_key)
                # Prevent negative values
                if new_value < 0:
                    cache.set(cache_key, 0, timeout=60)
            else:
                # Fallback for non-Redis (development)
                current = cache.get(cache_key, 0)
                if current > 0:
                    cache.set(cache_key, current - 1, timeout=60)
        except Exception as e:
            logger.error(f"Failed to decrement global counter: {e}")
    
    def _check_user_minute_limit(self, user_id):
        """Check and update per-user minute rate limit atomically."""
        cache_key = f"{CACHE_PREFIX_MINUTE}{user_id}"
        
        if _is_redis_cache():
            # Redis atomic operations
            try:
                current_count = cache.get(cache_key, 0)
                if current_count >= USER_REQUESTS_PER_MINUTE:
                    return False
                
                # Atomic increment
                cache.incr(cache_key)
                # Set expiry only if key is new
                if current_count == 0:
                    cache.expire(cache_key, 60)
                return True
            except Exception as e:
                logger.error(f"Redis error in minute limit: {e}")
                return True  # Fail open to not block users
        else:
            # Fallback for development
            current_count = cache.get(cache_key, 0)
            if current_count >= USER_REQUESTS_PER_MINUTE:
                return False
            cache.set(cache_key, current_count + 1, timeout=60)
            return True
    
    def _check_user_hour_limit(self, user_id):
        """Check and update per-user hourly rate limit atomically."""
        cache_key = f"{CACHE_PREFIX_HOUR}{user_id}"
        
        if _is_redis_cache():
            # Redis atomic operations
            try:
                current_count = cache.get(cache_key, 0)
                if current_count >= USER_REQUESTS_PER_HOUR:
                    return False
                
                # Atomic increment
                cache.incr(cache_key)
                # Set expiry only if key is new
                if current_count == 0:
                    cache.expire(cache_key, 3600)
                return True
            except Exception as e:
                logger.error(f"Redis error in hour limit: {e}")
                return True  # Fail open to not block users
        else:
            # Fallback for development
            current_count = cache.get(cache_key, 0)
            if current_count >= USER_REQUESTS_PER_HOUR:
                return False
            cache.set(cache_key, current_count + 1, timeout=3600)
            return True
    
    def _rate_limit_response(self, message, retry_after=60):
        """Generate a rate limit response."""
        # Check if this is an HTMX request
        is_htmx = 'HX-Request' in self.get_response.__self__.META if hasattr(self.get_response, '__self__') else False
        
        # For HTMX requests, return HTML partial
        # For API requests, return JSON
        response = JsonResponse({
            'error': 'rate_limit_exceeded',
            'message': message,
            'retry_after': retry_after
        }, status=429)
        
        response['Retry-After'] = str(retry_after)
        return response


class APIRateLimitMiddleware:
    """
    Additional rate limiting specifically for AI API calls.
    
    This provides an extra layer of protection for expensive API operations
    beyond the general request rate limiting.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only apply to chat message endpoints
        if request.method == 'POST' and '/chat/' in request.path and request.POST.get('message'):
            if not self._check_api_rate_limit(request.user.id):
                logger.warning(f"User {request.user.id} exceeded API rate limit")
                return JsonResponse({
                    'error': 'api_rate_limit',
                    'message': 'AI API rate limit reached. Please wait before sending another message.',
                    'retry_after': 30
                }, status=429)
        
        return self.get_response(request)
    
    def _check_api_rate_limit(self, user_id):
        """
        Check API-specific rate limit atomically.
        More restrictive than general rate limit.
        Allows 5 AI calls per minute per user.
        """
        cache_key = f"api_rate_limit_{user_id}"
        
        if _is_redis_cache():
            # Redis atomic operations
            try:
                current_count = cache.get(cache_key, 0)
                if current_count >= 5:  # 5 AI calls per minute
                    return False
                
                # Atomic increment
                cache.incr(cache_key)
                # Set expiry only if key is new
                if current_count == 0:
                    cache.expire(cache_key, 60)
                return True
            except Exception as e:
                logger.error(f"Redis error in API limit: {e}")
                return True  # Fail open to not block users
        else:
            # Fallback for development
            current_count = cache.get(cache_key, 0)
            if current_count >= 5:
                return False
            cache.set(cache_key, current_count + 1, timeout=60)
            return True

"""Multi-Model Fallback System for the Nexus application.

This module implements a production-grade model hierarchy with automatic
fallback logic. When rate limits or errors occur, it cascades through
models from most powerful to lightest.

The fallback system supports:
    - 12 AI models from Gemini 3 Flash to Gemma 3 1B
    - Automatic retry with exponential backoff
    - Global exhaustion tracking with automatic reset
    - Graceful error handling and logging

Classes:
    ModelExhaustionError: Exception raised when all models are exhausted.

Functions:
    reset_exhaustion_if_needed: Reset exhaustion flag after timeout.
    is_rate_limit_error: Check if an error indicates rate limiting.
    is_fallback_error: Check if an error should trigger model fallback.
    generate_with_fallback: Generate AI response with automatic fallback.
    get_model_display_name: Convert model ID to user-friendly name.
    check_service_availability: Check if AI service is available.

Constants:
    MODEL_HIERARCHY: Ordered list of models from most to least powerful.
    EXHAUSTION_RESET_TIME: Seconds before resetting exhaustion status.
    MAX_RETRIES_PER_MODEL: Number of retries per model.
    INITIAL_RETRY_DELAY: Base delay for exponential backoff.
"""

import os
import logging
import time
from google import genai
from django.core.cache import cache
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Model hierarchy from most powerful to lightest
# Use actual available models from Google Gen AI API
MODEL_HIERARCHY = [
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemma-3-27b",
    "gemma-3-12b",
    "gemma-3-4b",
    "gemma-3-2b",
    "gemma-3-1b",
]

# Cache keys for rate limit exhaustion (shared across all workers)
CACHE_KEY_EXHAUSTED = "model_fallback_exhausted"
EXHAUSTION_RESET_TIME = 300  # Reset after 5 minutes

# Retry settings for transient errors
MAX_RETRIES_PER_MODEL = 2
INITIAL_RETRY_DELAY = 0.5  # seconds


class ModelExhaustionError(Exception):
    """Exception raised when all models in the hierarchy have been exhausted.

    This exception is raised when every model in the MODEL_HIERARCHY has
    failed due to rate limits or other recoverable errors, indicating
    the service is temporarily unavailable.
    """

    pass


def is_models_exhausted():
    """Check if all models are currently exhausted.

    Uses Django cache to check exhaustion state shared across workers.

    Returns:
        bool: True if all models are exhausted, False otherwise.
    """
    return cache.get(CACHE_KEY_EXHAUSTED, False)


def set_models_exhausted():
    """Mark all models as exhausted in the cache.

    Sets a cache key that expires after EXHAUSTION_RESET_TIME seconds,
    providing automatic recovery without manual intervention.
    """
    cache.set(CACHE_KEY_EXHAUSTED, True, timeout=EXHAUSTION_RESET_TIME)
    logger.warning(
        "All models exhausted, cache flag set for %ds", EXHAUSTION_RESET_TIME
    )


def is_rate_limit_error(error_str):
    """Check if an error string indicates a rate limit or transient error.

    Examines the error message for common rate limit and temporary
    unavailability indicators.

    Args:
        error_str: The error message string to check.

    Returns:
        bool: True if the error indicates rate limiting or temporary
            unavailability, False otherwise.
    """
    error_lower = error_str.lower()
    return any(
        keyword in error_lower
        for keyword in [
            "429",
            "503",
            "rate limit",
            "quota",
            "overloaded",
            "temporarily unavailable",
            "too many requests",
        ]
    )


def is_fallback_error(error_str):
    """Check if an error should trigger fallback to the next model.

    Determines if an error is recoverable and should cause the system
    to try the next model in the hierarchy. This includes rate limits,
    model not found errors, and temporary unavailability.

    Args:
        error_str: The error message string to check.

    Returns:
        bool: True if the error should trigger fallback to the next
            model, False for non-recoverable errors.
    """
    error_lower = error_str.lower()
    return any(
        keyword in error_lower
        for keyword in [
            "404",
            "not found",
            "not_found",
            "not supported",
            "not available",
            "429",
            "503",
            "rate limit",
            "quota",
            "overloaded",
            "temporarily unavailable",
            "too many requests",
        ]
    )


def generate_with_fallback(prompt, system_instruction=""):
    """Generate an AI response with automatic model fallback.

    Attempts to generate a response using models in the hierarchy,
    starting from the most powerful. If a model fails due to rate
    limits or unavailability, automatically falls back to the next
    model in the hierarchy.

    Args:
        prompt: The user's prompt or question to send to the AI.
        system_instruction: Optional system instruction for context.
            Defaults to an empty string.

    Returns:
        tuple: A tuple of (response_text, model_used) where:
            - response_text (str): The generated AI response.
            - model_used (str): The internal name of the model that
                successfully generated the response.

    Raises:
        ModelExhaustionError: If all models in the hierarchy fail due
            to rate limits or temporary unavailability.
        Exception: For non-recoverable errors such as API key issues
            or authentication failures.
    """
    # If all models were exhausted recently, fail fast (cache auto-expires)
    if is_models_exhausted():
        logger.warning("All models exhausted, rejecting request")
        raise ModelExhaustionError(
            "All model rate limits reached. Please try again later."
        )

    # Initialize client
    try:
        # Create client with API key - works for Gemini Developer API
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        logger.error("Failed to initialize Gemini client: %s", e)
        raise Exception("API configuration error. Please contact administrator.") from e

    # Build the full prompt with system instruction
    full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt

    # Try each model in the hierarchy
    for model_index, model_name in enumerate(MODEL_HIERARCHY):
        logger.info(
            "Attempting model %s/%s: %s",
            model_index + 1,
            len(MODEL_HIERARCHY),
            model_name,
        )

        # Try this model with retries for transient errors
        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=full_prompt
                )

                # Success! Return the response and model used
                logger.info("Success with %s on attempt %s", model_name, attempt + 1)
                return response.text, model_name

            except Exception as e:
                error_str = str(e)
                last_error = e

                # Check if this error should trigger fallback
                if is_fallback_error(error_str):
                    # This is a recoverable error (rate limit, not found, etc.)
                    if "404" in error_str or "not found" in error_str.lower():
                        logger.warning(
                            "Model %s not available (404): %s... Moving to next model",
                            model_name,
                            error_str[:100],
                        )
                        # Don't retry 404s, move to next model immediately
                        break
                    elif is_rate_limit_error(error_str):
                        logger.warning(
                            "Rate limit hit for %s (attempt %s/%s): %s...",
                            model_name,
                            attempt + 1,
                            MAX_RETRIES_PER_MODEL,
                            error_str[:100],
                        )
                        # If this is not the last retry for this model, wait and retry
                        if attempt < MAX_RETRIES_PER_MODEL - 1:
                            delay = INITIAL_RETRY_DELAY * (2**attempt)
                            logger.info("Retrying %s in %ss...", model_name, delay)
                            time.sleep(delay)
                            continue
                        else:
                            # Max retries for this model reached, move to next model
                            logger.warning(
                                "Max retries reached for %s, moving to next model",
                                model_name,
                            )
                            break
                    else:
                        # Other fallback error, move to next model
                        logger.warning(
                            "Error with %s: %s... Moving to next model",
                            model_name,
                            error_str[:100],
                        )
                        break
                else:
                    # Non-recoverable error (API key issues, etc.)
                    logger.error(
                        "Non-recoverable error with %s: %s", model_name, error_str
                    )
                    raise

    # If we get here, all models failed with rate limits
    logger.error("All %s models exhausted", len(MODEL_HIERARCHY))
    set_models_exhausted()

    raise ModelExhaustionError(
        "Service temporarily unavailable. All model rate limits reached. Please try again later."
    )


def get_model_display_name(model_name):
    """Convert an internal model name to a user-friendly display name.

    Translates technical model identifiers into human-readable names
    for display in the user interface.

    Args:
        model_name: The internal model identifier (e.g., 'gemini-2.5-flash').

    Returns:
        str: The user-friendly display name (e.g., 'Gemini 2.5 Flash').
            Returns the original model_name if no mapping exists.
    """
    name_map = {
        "gemini-3-flash-preview": "Gemini 3 Flash",
        "gemini-flash-latest": "Gemini Flash Latest",
        "gemini-2.5-flash": "Gemini 2.5 Flash",
        "gemini-2.0-flash": "Gemini 2.0 Flash",
        "gemini-flash-lite-latest": "Gemini Flash Lite Latest",
        "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
        "gemini-2.0-flash-lite": "Gemini 2.0 Flash Lite",
        "gemma-3-27b": "Gemma 3 27B",
        "gemma-3-12b": "Gemma 3 12B",
        "gemma-3-4b": "Gemma 3 4B",
        "gemma-3-2b": "Gemma 3 2B",
        "gemma-3-1b": "Gemma 3 1B",
    }
    return name_map.get(model_name, model_name)


def check_service_availability():
    """Check if the AI service is currently available.

    Checks the cache-based model exhaustion status to determine if AI
    responses can be generated. The cache auto-expires after
    EXHAUSTION_RESET_TIME seconds.

    Returns:
        tuple: A tuple of (is_available, message) where:
            - is_available (bool): True if service can accept requests.
            - message (str): Status message describing availability.
    """
    if is_models_exhausted():
        return (
            False,
            "Service temporarily unavailable. Please try again in a few minutes.",
        )

    return True, "Service available"

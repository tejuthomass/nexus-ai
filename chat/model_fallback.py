"""
Multi-Model Fallback System for Nexus AI

This module implements a production-grade model hierarchy with automatic fallback logic.
When rate limits or errors occur, it cascades through models from most powerful to lightest.
"""

import os
import logging
import time
from google import genai
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
    "gemma-3-1b"
]

# Track global rate limit exhaustion (shared across all users)
_all_models_exhausted = False
_exhaustion_timestamp = None
EXHAUSTION_RESET_TIME = 300  # Reset after 5 minutes

# Retry settings for transient errors
MAX_RETRIES_PER_MODEL = 2
INITIAL_RETRY_DELAY = 0.5  # seconds


class ModelExhaustionError(Exception):
    """Raised when all models in the hierarchy have been exhausted."""
    pass


def reset_exhaustion_if_needed():
    """Reset the exhaustion flag if enough time has passed."""
    global _all_models_exhausted, _exhaustion_timestamp
    
    if _all_models_exhausted and _exhaustion_timestamp:
        elapsed = time.time() - _exhaustion_timestamp
        if elapsed > EXHAUSTION_RESET_TIME:
            logger.info(f"Resetting model exhaustion after {elapsed:.0f}s")
            _all_models_exhausted = False
            _exhaustion_timestamp = None


def is_rate_limit_error(error_str):
    """Check if an error is a rate limit or transient error."""
    error_lower = error_str.lower()
    return any(keyword in error_lower for keyword in [
        '429',
        '503',
        'rate limit',
        'quota',
        'overloaded',
        'temporarily unavailable',
        'too many requests'
    ])


def is_fallback_error(error_str):
    """Check if an error should trigger fallback to next model."""
    error_lower = error_str.lower()
    return any(keyword in error_lower for keyword in [
        '404',
        'not found',
        'not_found',
        'not supported',
        'not available',
        '429',
        '503',
        'rate limit',
        'quota',
        'overloaded',
        'temporarily unavailable',
        'too many requests'
    ])


def generate_with_fallback(prompt, system_instruction=""):
    """
    Generate AI response with automatic model fallback.
    
    Args:
        prompt: The user's prompt/question
        system_instruction: Optional system instruction for context
        
    Returns:
        tuple: (response_text, model_used)
        
    Raises:
        ModelExhaustionError: If all models are exhausted
        Exception: For non-recoverable errors
    """
    global _all_models_exhausted, _exhaustion_timestamp
    
    # Check if we should reset exhaustion
    reset_exhaustion_if_needed()
    
    # If all models were exhausted recently, fail fast
    if _all_models_exhausted:
        logger.warning("All models exhausted, rejecting request")
        raise ModelExhaustionError("All model rate limits reached. Please try again later.")
    
    # Initialize client
    try:
        # Create client with API key - works for Gemini Developer API
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        raise Exception("API configuration error. Please contact administrator.")
    
    # Build the full prompt with system instruction
    full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    
    # Try each model in the hierarchy
    last_error = None
    for model_index, model_name in enumerate(MODEL_HIERARCHY):
        logger.info(f"Attempting model {model_index + 1}/{len(MODEL_HIERARCHY)}: {model_name}")
        
        # Try this model with retries for transient errors
        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                
                # Success! Return the response and model used
                logger.info(f"Success with {model_name} on attempt {attempt + 1}")
                return response.text, model_name
                
            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Check if this error should trigger fallback
                if is_fallback_error(error_str):
                    # This is a recoverable error (rate limit, not found, etc.)
                    if '404' in error_str or 'not found' in error_str.lower():
                        logger.warning(
                            f"Model {model_name} not available (404): {error_str[:100]}... Moving to next model"
                        )
                        # Don't retry 404s, move to next model immediately
                        break
                    elif is_rate_limit_error(error_str):
                        logger.warning(
                            f"Rate limit hit for {model_name} (attempt {attempt + 1}/{MAX_RETRIES_PER_MODEL}): {error_str[:100]}..."
                        )
                        # If this is not the last retry for this model, wait and retry
                        if attempt < MAX_RETRIES_PER_MODEL - 1:
                            delay = INITIAL_RETRY_DELAY * (2 ** attempt)
                            logger.info(f"Retrying {model_name} in {delay}s...")
                            time.sleep(delay)
                            continue
                        else:
                            # Max retries for this model reached, move to next model
                            logger.warning(f"Max retries reached for {model_name}, moving to next model")
                            break
                    else:
                        # Other fallback error, move to next model
                        logger.warning(f"Error with {model_name}: {error_str[:100]}... Moving to next model")
                        break
                else:
                    # Non-recoverable error (API key issues, etc.)
                    logger.error(f"Non-recoverable error with {model_name}: {error_str}")
                    raise
    
    # If we get here, all models failed with rate limits
    logger.error(f"All {len(MODEL_HIERARCHY)} models exhausted")
    _all_models_exhausted = True
    _exhaustion_timestamp = time.time()
    
    raise ModelExhaustionError(
        "Service temporarily unavailable. All model rate limits reached. Please try again later."
    )


def get_model_display_name(model_name):
    """
    Convert internal model name to user-friendly display name.
    
    Args:
        model_name: Internal model identifier
        
    Returns:
        str: User-friendly model name
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
        "gemma-3-1b": "Gemma 3 1B"
    }
    return name_map.get(model_name, model_name)


def check_service_availability():
    """
    Check if the AI service is currently available.
    
    Returns:
        tuple: (is_available: bool, message: str)
    """
    reset_exhaustion_if_needed()
    
    if _all_models_exhausted:
        time_since_exhaustion = time.time() - _exhaustion_timestamp if _exhaustion_timestamp else 0
        time_remaining = max(0, EXHAUSTION_RESET_TIME - time_since_exhaustion)
        return False, f"Service temporarily unavailable. Please try again in {int(time_remaining)}s."
    
    return True, "Service available"

# Multi-Model Fallback System Documentation

## Overview
This document describes the production-grade multi-model fallback system implemented in Nexus AI. The system automatically cascades through multiple AI models when rate limits or errors occur, ensuring maximum service availability.

## Architecture

### Model Hierarchy
Models are ordered from most powerful to lightest:

1. **gemini-exp-1206** (Primary) - Most powerful, experimental features
2. **gemini-2.0-flash-exp** (Secondary) - Balanced performance
3. **gemini-2.0-flash-thinking-exp** (Tertiary) - Reasoning-focused
4. **gemini-1.5-flash** (Quaternary) - Stable, reliable
5. **gemini-1.5-flash-8b** (Final fallback) - Lightweight, highest availability

### Fallback Logic

```
User Request
    ↓
Try Model 1 (gemini-exp-1206)
    ↓
Rate Limit? → Try Model 2 (gemini-2.0-flash-exp)
    ↓
Rate Limit? → Try Model 3 (gemini-2.0-flash-thinking-exp)
    ↓
Rate Limit? → Try Model 4 (gemini-1.5-flash)
    ↓
Rate Limit? → Try Model 5 (gemini-1.5-flash-8b)
    ↓
All Failed? → Disable Chat Interface
```

## Key Features

### 1. Automatic Fallback
- **Silent switching**: No verbose "switching models" messages
- **Immediate cascade**: On rate limit/error, immediately tries next model
- **Retry logic**: Each model gets 2 attempts before falling back
- **Exponential backoff**: 0.5s, 1s delays between retries

### 2. Global Rate Limit Tracking
- Tracks when ALL models are exhausted
- Disables chat interface across all users
- Auto-resets after 5 minutes
- Periodic availability checks (every 60s)

### 3. Clean User Experience
- **No visible model selection**: Users never choose models manually
- **Minimal UI**: Model name removed from main interface
- **Hover info**: Small info icon shows which model responded
- **Professional loading**: Simple "Processing..." message
- **Clear exhaustion state**: Disabled input with clear explanation

### 4. Error Handling
- **Rate limit errors**: Silent fallback to next model
- **API errors**: Proper error messages to user
- **Transient errors**: Automatic retry with exponential backoff
- **Non-recoverable errors**: Immediate failure with clear message

## Implementation Details

### Backend Components

#### 1. `chat/model_fallback.py`
Core fallback system implementation:

```python
generate_with_fallback(prompt, system_instruction)
# Returns: (response_text, model_used)
# Raises: ModelExhaustionError if all models fail
```

Key functions:
- `generate_with_fallback()`: Main entry point
- `is_rate_limit_error()`: Detects rate limit errors
- `check_service_availability()`: Checks if service is available
- `get_model_display_name()`: Maps model IDs to friendly names

#### 2. `chat/views.py`
Updated to use fallback system:
- Removed old retry logic
- Integrated `generate_with_fallback()`
- Handles `ModelExhaustionError`
- Returns model info with responses

#### 3. `chat/urls.py`
Added endpoint:
- `/api/check-availability/`: Returns service availability status

### Frontend Components

#### 1. Updated Templates
- **index.html**: Removed visible model name, added availability checking
- **message.html**: Added hover tooltip for model info
- **system_message.html**: Handles disable_chat flag

#### 2. JavaScript Enhancements
```javascript
// Functions added:
- disableChatInterface()  // Disables input when exhausted
- enableChatInterface()   // Re-enables when available
- checkServiceAvailability()  // Polls availability endpoint
```

#### 3. UI States

**Normal Operation:**
- Clean interface, no model name shown
- Simple "Processing..." loading state
- Small info icon on hover shows model used

**Exhaustion State:**
- Red warning banner: "Service temporarily unavailable..."
- Input field disabled with grayed-out appearance
- Submit button disabled
- Auto-checks availability every 30 seconds

## Configuration

### Model Hierarchy Customization
Edit `MODEL_HIERARCHY` in `chat/model_fallback.py`:

```python
MODEL_HIERARCHY = [
    "gemini-exp-1206",           # Primary
    "gemini-2.0-flash-exp",      # Secondary
    "gemini-2.0-flash-thinking-exp",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",       # Final fallback
]
```

### Timing Parameters
```python
MAX_RETRIES_PER_MODEL = 2        # Attempts per model
INITIAL_RETRY_DELAY = 0.5        # Seconds before first retry
EXHAUSTION_RESET_TIME = 300      # 5 minutes
```

## Testing

### Manual Testing Scenarios

1. **Normal Operation**
   - Send a message
   - Verify response appears
   - Hover over info icon to see model name

2. **Rate Limit Simulation**
   - If you have API access, temporarily reduce quota
   - Send messages to trigger fallback
   - Verify silent switching between models

3. **Complete Exhaustion**
   - Wait until all models hit rate limits
   - Verify chat interface disables
   - Check error message displays correctly
   - Wait 5 minutes and verify auto-recovery

4. **Page Reload During Exhaustion**
   - Trigger exhaustion state
   - Reload page
   - Verify chat remains disabled

### Logging
Monitor logs for fallback behavior:
```bash
# Watch for these log entries:
"Attempting model 1/5: gemini-exp-1206"
"Rate limit hit for gemini-exp-1206"
"Success with gemini-2.0-flash-exp on attempt 1"
"All 5 models exhausted"
```

## Production Considerations

### Monitoring
Track these metrics:
- Model usage distribution
- Fallback frequency
- Average latency per model
- Exhaustion events

### Rate Limit Management
- Global API key shared across all users
- Consider user-based queuing during high load
- Monitor quota usage via Google Cloud Console

### Scalability
Current implementation handles:
- Multiple concurrent users
- Graceful degradation under load
- Automatic recovery

For high-traffic scenarios, consider:
- Redis for distributed state tracking
- WebSocket notifications for real-time availability updates
- User-tier based priority queueing

## Troubleshooting

### Chat Interface Won't Enable
1. Check `/api/check-availability/` endpoint
2. Verify `_all_models_exhausted` flag in logs
3. Check if 5 minutes have passed since exhaustion
4. Restart Django server to force reset

### Model Not Falling Back
1. Check error message in logs
2. Verify error is rate limit (429, 503)
3. Ensure `is_rate_limit_error()` detects it
4. Check `MAX_RETRIES_PER_MODEL` setting

### Hover Tooltip Not Showing
1. Verify `model_used` passed to template
2. Check browser console for JavaScript errors
3. Inspect element for `group/model` hover class

## Future Enhancements

### Possible Improvements
1. **User-based rate limiting**: Track per-user quotas
2. **Smart model selection**: ML-based model routing
3. **Cost optimization**: Choose cheapest model first
4. **Queue system**: Fair queuing during exhaustion
5. **WebSocket updates**: Real-time availability notifications
6. **Analytics dashboard**: Model usage and performance metrics

## API Reference

### Backend

#### `generate_with_fallback(prompt, system_instruction="")`
Generates AI response with automatic model fallback.

**Parameters:**
- `prompt` (str): User's question/prompt
- `system_instruction` (str): Optional system context

**Returns:**
- `tuple`: (response_text: str, model_used: str)

**Raises:**
- `ModelExhaustionError`: All models exhausted
- `Exception`: Non-recoverable errors

#### `check_service_availability()`
Checks if AI service is currently available.

**Returns:**
- `tuple`: (is_available: bool, message: str)

### Frontend

#### `/api/check-availability/`
REST endpoint for checking service availability.

**Method:** GET

**Response:**
```json
{
    "available": true,
    "message": "Service available"
}
```

## Changelog

### Version 1.0.0 (January 2026)
- Initial implementation
- 5-model hierarchy
- Global exhaustion tracking
- Clean UI with hover tooltips
- Automatic availability checking
- Production-grade error handling

## Support

For issues or questions:
1. Check logs in `/var/log/` or Django console
2. Verify API key configuration in `.env`
3. Test `/api/check-availability/` endpoint
4. Review this documentation

---

**Last Updated:** January 28, 2026
**Version:** 1.0.0

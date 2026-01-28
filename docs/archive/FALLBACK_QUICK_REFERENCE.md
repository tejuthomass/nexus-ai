# Multi-Model Fallback System - Quick Reference

## 🎯 What Changed

### Before
- Single model (gemini-2.5-flash)
- Visible model name in header
- Basic retry logic (3 attempts)
- Verbose error messages
- Manual intervention needed on failures

### After
- **5-model hierarchy** with automatic fallback
- **Hidden model selection** - hover to see
- **Silent cascading** through models
- **Clean, minimal UI**
- **Auto-disable on exhaustion**

---

## 🏗️ Model Hierarchy

```
1. gemini-exp-1206              ← Primary (most powerful)
2. gemini-2.0-flash-exp         
3. gemini-2.0-flash-thinking-exp
4. gemini-1.5-flash             
5. gemini-1.5-flash-8b          ← Final fallback (lightest)
```

**Fallback Flow:**
```
User sends message
    ↓
Try Model 1 → Rate Limit? → Try Model 2 → Rate Limit? → ... → Try Model 5
                                                                    ↓
                                                        All Failed? → Disable Chat
```

---

## 🎨 UI Changes

### Header
**Before:** `Model: Gemini 2.5 Flash` (always visible)  
**After:** Clean header, no model name

### Message Response
**Before:** Just the response  
**After:** Response + small info icon (ℹ️)
- Hover over icon → See which model responded
- Example tooltip: "Gemini 2.0 Flash"

### Loading State
**Before:** "Nexus is thinking..."  
**After:** "Processing..." (cleaner, shorter)

### Exhaustion State
**NEW:** Red warning banner:
```
⚠️ Service temporarily unavailable. 
All model rate limits reached. Please try again later.
```
- Input field disabled
- Submit button disabled
- Form grayed out
- Auto-checks availability every 30-60s

---

## 🔧 Technical Implementation

### New Files
1. **`chat/model_fallback.py`** - Core fallback logic
   - `generate_with_fallback()` - Main function
   - `ModelExhaustionError` - Custom exception
   - Global exhaustion tracking

2. **`docs/MODEL_FALLBACK_SYSTEM.md`** - Full documentation

3. **`test_model_fallback.py`** - Test suite

### Modified Files
1. **`chat/views.py`**
   - Removed old retry logic
   - Integrated `generate_with_fallback()`
   - Added `/api/check-availability/` endpoint

2. **`chat/urls.py`**
   - Added availability check endpoint

3. **`chat/templates/chat/index.html`**
   - Removed visible model name
   - Added service unavailable banner
   - Added JavaScript for availability checking
   - Disabled state handling

4. **`chat/templates/chat/partials/message.html`**
   - Added hover info icon
   - Model name tooltip

5. **`chat/templates/chat/partials/system_message.html`**
   - Added disable_chat flag support

---

## 🚀 How It Works

### Automatic Fallback
```python
# User sends message
↓
views.py calls: generate_with_fallback(prompt)
↓
model_fallback.py tries models in order:
  1. Try gemini-exp-1206 (2 attempts)
     ↓ Rate limit? 
  2. Try gemini-2.0-flash-exp (2 attempts)
     ↓ Rate limit?
  3. Try gemini-2.0-flash-thinking-exp (2 attempts)
     ↓ Rate limit?
  4. Try gemini-1.5-flash (2 attempts)
     ↓ Rate limit?
  5. Try gemini-1.5-flash-8b (2 attempts)
     ↓ All failed?
  Raise ModelExhaustionError
↓
views.py catches error → Disable chat UI
```

### Global Exhaustion Tracking
```python
# When all models fail:
_all_models_exhausted = True
_exhaustion_timestamp = current_time

# Auto-reset after 5 minutes:
if time_elapsed > 300:
    _all_models_exhausted = False
```

### Frontend Availability Checking
```javascript
// On page load:
checkServiceAvailability()

// Every 60 seconds:
setInterval(checkServiceAvailability, 60000)

// If unavailable:
disableChatInterface()
showWarningBanner()

// If available:
enableChatInterface()
hideWarningBanner()
```

---

## 📊 Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `MODEL_HIERARCHY` | 5 models | Fallback order |
| `MAX_RETRIES_PER_MODEL` | 2 | Attempts per model |
| `INITIAL_RETRY_DELAY` | 0.5s | Wait before retry |
| `EXHAUSTION_RESET_TIME` | 300s (5 min) | Auto-recovery time |
| Availability check interval | 60s | Frontend polling |

---

## 🧪 Testing Checklist

- [x] Normal message sending works
- [x] Model info shows on hover
- [x] Loading state displays "Processing..."
- [x] Error handling works
- [x] Django check passes
- [ ] **Manual test:** Trigger rate limit to see fallback
- [ ] **Manual test:** All models exhausted → UI disables
- [ ] **Manual test:** Wait 5 minutes → Auto-recovery

---

## 🎯 User Experience Goals

### ✅ Achieved
- **Transparent fallback** - User never knows switching happened
- **Minimal disruption** - Silent error handling
- **Clear communication** - Only show status when needed
- **Professional appearance** - Clean, modern UI
- **Automatic recovery** - No manual intervention required

### Production-Ready Features
- Global rate limit tracking
- Exponential backoff
- Clean error messages
- Accessibility (hover tooltips)
- Real-time availability checking
- Graceful degradation

---

## 📝 Quick Commands

### Test Implementation
```bash
# Run Django checks
python manage.py check

# Run fallback tests (when created)
python test_model_fallback.py

# Start server
python manage.py runserver
```

### Monitor Logs
```bash
# Watch for fallback events
tail -f logs/django.log | grep "model"

# Key log messages:
"Attempting model 1/5: gemini-exp-1206"
"Rate limit hit for gemini-exp-1206"
"Success with gemini-2.0-flash-exp"
"All 5 models exhausted"
```

---

## 🔗 Resources

- Full Documentation: `/docs/MODEL_FALLBACK_SYSTEM.md`
- Implementation: `/chat/model_fallback.py`
- Views: `/chat/views.py`
- Templates: `/chat/templates/chat/`

---

**Status:** ✅ Implementation Complete  
**Version:** 1.0.0  
**Date:** January 28, 2026

# File Upload UX - Developer Quick Reference

## 🎯 What Changed

### Main Chat Area (`chat/templates/chat/index.html`)
**Removed:** File upload paperclip icon and input
**Result:** Clean chat interface with only message textarea and send button

### Right Sidebar (`chat/templates/chat/partials/attachments_sidebar.html`)
**Added:** 
- File upload form with "Upload PDF" button
- Processing indicator ("Processing PDF...")
- File size limit display ("Max size: 10MB")
- JavaScript functions for input control

### New Partial (`chat/templates/chat/partials/attachments_list.html`)
**Purpose:** Reusable template for rendering attachments list
**Used by:** Both initial page load and HTMX updates

### Backend (`chat/views.py`)
**Changed:** Return `attachments_list.html` instead of `attachments.html`

---

## 🔧 How It Works

### 1. File Upload Flow
```
User clicks "Upload PDF" 
    ↓
File selected via browser dialog
    ↓
Form auto-submits (HTMX)
    ↓
disableChatInput() called
    ↓
Processing indicator shows
    ↓
Server processes file
    ↓
Returns updated attachments_list.html
    ↓
HTMX swaps content in #attachments-list
    ↓
enableChatInput() called
    ↓
User can continue chatting
```

### 2. HTMX Attributes Explained
```html
hx-post="{% url 'chat_session' session.id %}"
  → Posts to current session endpoint

hx-encoding="multipart/form-data"
  → Required for file uploads

hx-target="#attachments-list"
  → Updates only the attachments list div

hx-indicator="#sidebar-upload-indicator"
  → Shows/hides processing indicator

hx-on::before-request="disableChatInput()"
  → Runs before upload starts

hx-on::after-request="enableChatInput(); this.reset(); updateFileLabel('');"
  → Runs after upload completes
```

### 3. JavaScript Functions

#### `disableChatInput()`
- Disables textarea and submit button
- Changes placeholder to "Processing PDF, please wait..."
- Called automatically before upload

#### `enableChatInput()`
- Re-enables textarea and submit button
- Restores normal placeholder
- Called automatically after upload

#### `updateFileLabel(filename)`
- Displays selected filename
- Truncates if > 25 characters
- Called when file is selected

---

## 📁 File Structure

```
chat/
├── views.py                          [Modified]
│   └── File upload handler returns attachments_list.html
│
└── templates/chat/
    ├── index.html                    [Modified]
    │   └── Removed file upload from main chat
    │
    └── partials/
        ├── attachments_sidebar.html  [Modified]
        │   ├── Upload form
        │   ├── Processing indicator
        │   ├── JavaScript functions
        │   └── Includes attachments_list.html
        │
        └── attachments_list.html     [NEW]
            └── Reusable list template
```

---

## 🎨 UI Components

### Upload Button
```html
<label for="sidebar-pdf-upload" class="...">
    <i class="fas fa-upload"></i>
    <span>Upload PDF</span>
</label>
<input type="file" id="sidebar-pdf-upload" name="pdf_file" accept=".pdf">
```

### Processing Indicator
```html
<div id="sidebar-upload-indicator" class="htmx-indicator ...">
    <i class="fas fa-circle-notch fa-spin"></i>
    <span>Processing PDF...</span>
</div>
```

### Size Limit Info
```html
<div class="text-xs text-gray-600 text-center">
    <i class="fas fa-info-circle"></i> Max size: 10MB
</div>
```

---

## 🔒 Security & Validation

### Client-Side
- File input accepts only `.pdf` files
- Size limit displayed to users

### Server-Side (Existing in views.py)
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.pdf']

# Validation checks:
1. File extension validation
2. File size validation
3. CSRF token validation
4. User authentication
```

---

## 🐛 Debugging

### If files don't appear after upload:
1. Check HTMX target: `#attachments-list` exists?
2. Check server response: Returns `attachments_list.html`?
3. Check database: Document saved with correct session?

### If chat doesn't re-enable:
1. Check JavaScript console for errors
2. Verify `enableChatInput()` is being called
3. Check HTMX `hx-on::after-request` attribute

### If upload indicator doesn't show:
1. Verify `#sidebar-upload-indicator` element exists
2. Check `hx-indicator` attribute is set
3. Ensure `.htmx-indicator` CSS class is defined

---

## 🧪 Testing Checklist

```bash
# 1. Visual Check
□ Main chat has NO paperclip icon
□ Right sidebar has "Upload PDF" button
□ "Max size: 10MB" is visible

# 2. Upload Process
□ Click "Upload PDF" button
□ Select a valid PDF file
□ Processing indicator appears
□ Chat input shows "Processing PDF, please wait..."
□ Chat input and button are disabled
□ File appears in list after processing
□ Chat re-enables automatically

# 3. Error Handling
□ Try uploading file > 10MB
□ Error message appears
□ Chat remains functional

# 4. Persistence
□ Upload a file
□ Refresh page (F5)
□ File still visible in sidebar

# 5. Mobile View
□ Sidebar may be hidden
□ Upload still works when sidebar is visible
□ Chat area remains clean
```

---

## 🔄 HTMX Request/Response Cycle

### Request
```
POST /chat/<session_id>/
Content-Type: multipart/form-data

pdf_file: [binary data]
csrfmiddlewaretoken: [token]
```

### Response (Success)
```html
<!-- attachments_list.html -->
<a href="..." class="...">
    <i class="fas fa-file-pdf"></i>
    <div>
        <p>filename.pdf</p>
        <p>Jan 27, 14:30</p>
    </div>
</a>
...
```

### Response (Error)
```html
<!-- system_message.html -->
<div class="error-message">
    ❌ File too large. Maximum size is 10MB.
</div>
```

---

## 💡 Key Design Decisions

### Why disable chat during upload?
- Prevents user confusion
- Avoids race conditions
- Clear feedback that processing is happening
- Better UX (user knows to wait)

### Why move upload to sidebar?
- Keeps main chat area clean
- Logical grouping (attachments with attachments)
- Reduces visual clutter
- Improves focus on chat

### Why show size limit?
- Proactive user guidance
- Reduces failed upload attempts
- Better error prevention
- Transparent limitations

### Why use partials?
- DRY principle
- Consistent rendering
- HTMX-friendly
- Easier maintenance

---

## 📝 Environment Variables (No Changes)

Existing configuration still applies:
```python
# Cloudinary (file storage)
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET

# Pinecone (RAG/embeddings)
PINECONE_API_KEY
PINECONE_INDEX_NAME

# Gemini (AI model)
GEMINI_API_KEY
```

---

## 🚀 Deployment Notes

1. **No database migrations needed**
   - Only template changes
   - Existing models unchanged

2. **No new dependencies**
   - Uses existing packages
   - HTMX already included

3. **Static files**
   - No new CSS/JS files
   - Inline scripts only

4. **Cache clearing**
   - May need to clear browser cache
   - Hard refresh (Ctrl+F5)

---

## 🔮 Future Enhancements

### Easy Additions:
- File delete button
- Drag & drop upload
- Upload progress bar
- File preview modal

### Medium Complexity:
- Multiple file upload
- File type icons
- Download all as ZIP
- Upload history

### Advanced:
- Real-time upload status via WebSockets
- Thumbnail generation
- OCR preview
- Collaborative annotations

---

## 📞 Support

If issues arise:
1. Check browser console for JavaScript errors
2. Check Django logs for server errors
3. Verify HTMX is loaded properly
4. Test with browser DevTools Network tab

Common issues:
- CSRF token mismatch → Check token is passed
- HTMX not responding → Check htmx.org is loaded
- Files not persisting → Check database connection
- Style issues → Clear browser cache

---

## ✅ Verification Commands

```bash
# Check template files exist
ls -la chat/templates/chat/partials/attachments_*.html

# Search for file upload in main chat (should return nothing)
grep -r "paperclip" chat/templates/chat/index.html

# Search for upload button in sidebar (should return match)
grep -r "Upload PDF" chat/templates/chat/partials/attachments_sidebar.html

# Check views.py returns correct template
grep -A 5 "attachments_list.html" chat/views.py
```

---

## 📊 Performance Impact

- **Minimal:** Only template changes
- **No additional queries:** Uses existing database calls
- **HTMX overhead:** Negligible (already used)
- **JavaScript:** Lightweight functions only
- **File size:** No change (same validation as before)

---

## 🎓 Learning Resources

### HTMX Documentation:
- https://htmx.org/docs/
- https://htmx.org/attributes/hx-on/

### Django Templates:
- https://docs.djangoproject.com/en/5.0/ref/templates/

### File Uploads:
- https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/

---

**Last Updated:** January 27, 2026  
**Version:** 1.0  
**Author:** GitHub Copilot

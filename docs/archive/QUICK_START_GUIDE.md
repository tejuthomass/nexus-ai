# 🚀 Quick Start Guide - File Upload Feature

## For End Users

### How to Upload a PDF File

1. **Open Nexus AI** in your browser
2. **Log in** to your account
3. **Look at the right sidebar** (labeled "ATTACHMENTS")
4. **Click the green "Upload PDF" button**
5. **Select a PDF file** from your computer (max 10MB)
6. **Wait for processing** (you'll see "Processing PDF..." indicator)
7. **Done!** Your file appears in the attachments list

### What to Expect

- ✅ Chat input will be disabled while file uploads
- ✅ You'll see "Processing PDF, please wait..." message
- ✅ A spinning indicator shows progress
- ✅ File appears in list when complete
- ✅ Chat automatically re-enables when done
- ✅ File persists even if you refresh the page

### Tips

- **File size limit:** 10MB maximum
- **File type:** Only PDF files accepted
- **Upload location:** Right sidebar only (no icon in chat area)
- **Multiple files:** Upload one at a time
- **After upload:** You can immediately chat about the PDF content

---

## For Testers

### Testing Checklist

#### ✅ Basic Upload Test
```
1. Start on chat page
2. Verify NO paperclip icon in main chat area
3. Look at right sidebar
4. Confirm "Upload PDF" button is visible
5. Confirm "Max size: 10MB" text is visible
6. Click "Upload PDF" button
7. Select a valid PDF file (< 10MB)
8. Wait for processing
9. Verify file appears in attachments list
10. Verify chat input is re-enabled
```

#### ✅ Chat Disabling Test
```
1. Start upload process
2. During upload, try to type in chat input
3. Verify you CANNOT type (input is disabled)
4. Verify placeholder says "Processing PDF, please wait..."
5. Try clicking send button
6. Verify button is disabled (grayed out)
7. Wait for upload to complete
8. Verify chat input becomes enabled again
9. Verify placeholder returns to "Message Nexus..."
10. Type a message and confirm it works
```

#### ✅ Processing Indicator Test
```
1. Click "Upload PDF" and select file
2. Immediately look at right sidebar
3. Verify blue "Processing PDF..." box appears
4. Verify spinning icon is visible
5. Wait for upload to complete
6. Verify indicator disappears
7. Verify file appears in list
```

#### ✅ File Persistence Test
```
1. Upload a PDF file successfully
2. Verify file appears in attachments list
3. Note the filename and timestamp
4. Refresh the page (F5)
5. Verify file is STILL visible in attachments list
6. Verify filename and timestamp match
7. Click file link to verify download works
```

#### ✅ Error Handling Test
```
Test 1: File Too Large
1. Find or create a PDF file > 10MB
2. Try to upload it
3. Verify error message: "File too large. Maximum size is 10MB."
4. Verify chat input remains enabled

Test 2: Invalid File Type
1. Try to upload a .txt or .docx file
2. File picker should only show .pdf files
3. If you force wrong type, verify rejection

Test 3: Network Interruption
1. Start upload
2. Disconnect network mid-upload
3. Verify graceful error message
4. Verify chat remains functional
```

#### ✅ Mobile Responsiveness Test
```
1. Open on mobile device (or use DevTools mobile view)
2. Verify left sidebar can be toggled
3. Verify main chat is clean and functional
4. Toggle right sidebar if needed
5. Verify upload button is accessible
6. Test upload process on mobile
```

---

## For Developers

### Quick Code Review Checklist

```bash
# 1. Verify templates exist
ls chat/templates/chat/partials/attachments_sidebar.html
ls chat/templates/chat/partials/attachments_list.html

# 2. Check for paperclip in main chat (should be NONE)
grep -n "paperclip" chat/templates/chat/index.html

# 3. Verify upload button exists (should find it)
grep -n "Upload PDF" chat/templates/chat/partials/attachments_sidebar.html

# 4. Check JavaScript functions exist
grep -n "disableChatInput" chat/templates/chat/partials/attachments_sidebar.html
grep -n "enableChatInput" chat/templates/chat/partials/attachments_sidebar.html

# 5. Verify views return correct template
grep -n "attachments_list.html" chat/views.py
```

### Running the Server

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Run migrations (if needed)
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000

# Access in browser
# http://localhost:8000/
```

### Debugging Common Issues

#### Issue: "Upload button not showing"
```
Solution:
1. Check right sidebar is visible (>1024px width)
2. Verify attachments_sidebar.html is being included
3. Check browser console for errors
4. Verify session object is passed to template
```

#### Issue: "Chat doesn't re-enable after upload"
```
Solution:
1. Open browser console
2. Check for JavaScript errors
3. Verify enableChatInput() function exists
4. Check HTMX hx-on::after-request attribute
5. Verify HTMX is loaded correctly
```

#### Issue: "Files don't persist after reload"
```
Solution:
1. Check database: Document records exist?
2. Verify session filter is correct
3. Check Cloudinary file upload succeeded
4. Verify Document.file.url is valid
5. Check browser network tab for file URL
```

#### Issue: "Upload fails silently"
```
Solution:
1. Check Django logs for errors
2. Verify Cloudinary credentials in .env
3. Check Pinecone API key is valid
4. Verify database connection
5. Check file permissions
```

---

## For Product Managers

### Feature Summary

**What Changed:**
- File upload moved from main chat area to right sidebar
- Added clear processing indicators
- Implemented chat disabling during upload
- Added file size limit display (10MB)
- Fixed file persistence issues

**Benefits:**
- Cleaner, more focused chat interface
- Better user guidance and feedback
- Reduced user confusion
- More reliable file management
- Professional, polished experience

### User Stories Covered

1. ✅ **As a user**, I want a clean chat interface so I can focus on messaging
   - *Delivered:* Removed file upload from main area

2. ✅ **As a user**, I want to know when files are processing so I don't get confused
   - *Delivered:* Processing indicator and disabled chat input

3. ✅ **As a user**, I want to see the file size limit before uploading
   - *Delivered:* "Max size: 10MB" displayed prominently

4. ✅ **As a user**, I want my uploaded files to persist after page refresh
   - *Delivered:* Database-backed persistence working correctly

### Metrics to Track

1. **Upload Success Rate**
   - Target: >95% successful uploads
   - Track: Failed uploads / Total attempts

2. **User Confusion Incidents**
   - Target: <5% users confused about upload location
   - Track: Support tickets about file upload

3. **File Persistence Issues**
   - Target: 0 reports of files disappearing
   - Track: Bug reports about missing files

4. **Page Load Performance**
   - Target: No degradation
   - Track: Time to interactive

---

## For QA Engineers

### Test Cases

#### TC001: Upload Valid PDF
```
Preconditions: User logged in, on chat page
Steps:
1. Click "Upload PDF" in right sidebar
2. Select valid PDF file (< 10MB)
3. Wait for upload to complete

Expected Results:
- Processing indicator appears during upload
- Chat input is disabled during upload
- File appears in attachments list
- Chat input re-enables after upload
- File persists after page reload

Status: [ ] Pass [ ] Fail
Notes: _________________________
```

#### TC002: Upload Large PDF
```
Preconditions: User logged in, on chat page
Steps:
1. Click "Upload PDF" in right sidebar
2. Select PDF file (> 10MB)
3. Observe results

Expected Results:
- Error message: "File too large. Maximum size is 10MB."
- Chat input remains enabled
- No file added to list
- User can try again

Status: [ ] Pass [ ] Fail
Notes: _________________________
```

#### TC003: Chat During Upload
```
Preconditions: User logged in, on chat page
Steps:
1. Click "Upload PDF" in right sidebar
2. Select valid PDF file
3. Immediately try to type in chat input
4. Try to click send button

Expected Results:
- Chat input is disabled (cannot type)
- Placeholder text: "Processing PDF, please wait..."
- Send button is disabled
- Input re-enables after upload completes

Status: [ ] Pass [ ] Fail
Notes: _________________________
```

#### TC004: File Persistence
```
Preconditions: User logged in, on chat page
Steps:
1. Upload a PDF file successfully
2. Note filename and timestamp
3. Refresh page (F5)
4. Check right sidebar

Expected Results:
- File is still visible in attachments list
- Filename matches
- Timestamp matches
- File link is clickable and works

Status: [ ] Pass [ ] Fail
Notes: _________________________
```

#### TC005: Multiple Sessions
```
Preconditions: User logged in
Steps:
1. Upload file in Session A
2. Create new chat session (Session B)
3. Check right sidebar in Session B
4. Return to Session A
5. Check right sidebar in Session A

Expected Results:
- File in Session A not visible in Session B
- File in Session A still visible when returning
- Proper session isolation

Status: [ ] Pass [ ] Fail
Notes: _________________________
```

### Regression Tests

```
□ Chat messaging still works normally
□ New chat creation works
□ Chat history sidebar works
□ User logout works
□ Admin dashboard works (if admin)
□ AI responses generate correctly
□ RAG functionality works with uploaded files
□ Mobile view works correctly
□ Dark theme displays correctly
□ HTMX requests work throughout app
```

---

## For Support Teams

### Common User Questions

**Q: Where do I upload PDF files?**
A: Look at the right sidebar labeled "ATTACHMENTS". You'll see a green "Upload PDF" button there.

**Q: Why can't I type while uploading?**
A: This is by design! The chat input is temporarily disabled while your file is being processed. It will automatically re-enable when the upload completes.

**Q: What's the file size limit?**
A: 10MB maximum. You'll see this limit displayed in the right sidebar under the upload button.

**Q: My file disappeared after I refreshed the page!**
A: This should not happen anymore. If it does, please report it as a bug with these details:
   - When did you upload the file?
   - What was the filename?
   - Which browser are you using?
   - Can you reproduce the issue?

**Q: Can I upload multiple files at once?**
A: Currently, you can upload one file at a time. Upload your first file, wait for it to complete, then upload the next one.

**Q: What file types are supported?**
A: Only PDF files are currently supported.

**Q: Can I delete uploaded files?**
A: Not in the current version. Uploaded files remain associated with the chat session. (Future enhancement planned)

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│           FILE UPLOAD QUICK REFERENCE                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Where to Upload:     Right Sidebar → "Upload PDF"  │
│  File Size Limit:     10MB maximum                  │
│  Supported Types:     PDF only                      │
│  Upload Location:     Right sidebar ONLY            │
│                                                      │
│  During Upload:                                      │
│    • Processing indicator shows                     │
│    • Chat input disabled                            │
│    • Send button disabled                           │
│    • Wait for completion                            │
│                                                      │
│  After Upload:                                       │
│    • File appears in list                           │
│    • Chat automatically re-enables                  │
│    • File persists after refresh                    │
│                                                      │
│  Error Messages:                                     │
│    • "File too large" → Use file < 10MB            │
│    • "Invalid type" → Use PDF files only           │
│    • "Upload failed" → Try again                    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Troubleshooting Guide

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Upload button not visible | Screen too narrow | Increase browser width to >1024px |
| Upload fails | File too large | Use file < 10MB |
| Upload fails | Wrong file type | Use PDF file only |
| Chat won't re-enable | JavaScript error | Refresh page, check console |
| File disappeared | Database issue | Report bug, re-upload file |
| Processing stuck | Network issue | Refresh page, try again |
| Can't find upload | Looking in wrong place | Check RIGHT sidebar, not main chat |

---

## Video Tutorial Script (for training)

```
[00:00] "Welcome to Nexus AI's new file upload feature!"

[00:05] "To upload a PDF, look at the right sidebar..."
        [Point to right sidebar]

[00:10] "You'll see the 'Upload PDF' button here."
        [Highlight button]

[00:15] "Notice the file size limit is clearly shown: 10MB maximum."
        [Point to size limit text]

[00:20] "Click the Upload PDF button and select your file."
        [Demonstrate click and file selection]

[00:25] "While uploading, you'll see 'Processing PDF...' indicator."
        [Show indicator]

[00:30] "The chat input is temporarily disabled for clarity."
        [Show disabled input]

[00:35] "When complete, your file appears in the attachments list!"
        [Show file in list]

[00:40] "And the chat automatically re-enables so you can continue."
        [Show typing in chat]

[00:45] "Even if you refresh the page, your files persist!"
        [Demonstrate F5 refresh]

[00:50] "That's it! Simple, clear, and reliable file uploads in Nexus AI."
        [Show final result]
```

---

**Need Help?**
- Documentation: See `FILE_UPLOAD_UX_IMPROVEMENTS.md`
- Technical Details: See `DEVELOPER_REFERENCE_UPLOAD_UX.md`
- Architecture: See `ARCHITECTURE_DIAGRAM.md`
- Summary: See `IMPLEMENTATION_SUMMARY.md`

**Ready to Test!** 🚀

# Deployment & Testing Checklist

## Pre-Deployment Verification

### Code Quality
- [x] No syntax errors (Django check passed)
- [x] All imports valid
- [x] URLs properly configured
- [x] Views have required decorators
- [x] Template syntax correct

### Feature Testing Checklist

#### 1. Attachments Sidebar ✓
- [ ] Open a chat with PDF attachments
- [ ] Verify right sidebar displays on desktop
- [ ] Verify attachments list shows all PDFs
- [ ] Verify "No attachments" message on empty chats
- [ ] Click attachment links - should download
- [ ] Test on mobile - sidebar should be hidden
- [ ] Test on tablet - sidebar should be hidden
- [ ] Verify hover effects work (download icon appears)

#### 2. Loading Spinner Position ✓
- [ ] Upload a PDF to chat
- [ ] While uploading, send a message
- [ ] Verify "Nexus is thinking..." spinner is properly positioned
- [ ] Spinner should NOT overlap with messages
- [ ] Spinner should NOT appear off-screen
- [ ] Spinner should have consistent Z-index
- [ ] Multiple rapid uploads - verify consistent positioning
- [ ] Test across different browser zoom levels

#### 3. Admin Modal Interface ✓
- [ ] Login as admin user
- [ ] Navigate to Nexus Core dashboard
- [ ] Hover over a chat session
- [ ] Verify eye icon appears on hover
- [ ] Click eye icon
- [ ] Modal should appear inline (NOT new tab/window)
- [ ] Messages should populate from left side
- [ ] Attachments should show on right side
- [ ] Click modal close button - should close
- [ ] Click outside modal - should close
- [ ] Verify dark overlay appears behind modal
- [ ] Test modal on different screen sizes
- [ ] Click multiple chats - modal updates content
- [ ] Test with chats that have no attachments

#### 4. Naming: "God Mode" → "Nexus Core" ✓
- [ ] Main chat header button says "Nexus Core"
- [ ] Dashboard title says "Nexus Core"
- [ ] All documentation mentions "Nexus Core"
- [ ] Search codebase - no remaining "god mode" references
- [ ] Button icon remains shield icon
- [ ] Button styling consistent with design

### Browser Compatibility
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome
- [ ] Mobile Safari

### Responsive Design Testing
**Desktop (1920x1080)**
- [ ] All 3 columns visible
- [ ] Chat content readable
- [ ] Sidebar widths proportional
- [ ] No horizontal scrolling

**Laptop (1366x768)**
- [ ] All 3 columns visible
- [ ] Right sidebar visible
- [ ] No layout shifts

**Tablet (1024x768)**
- [ ] Left sidebar hidden or toggled
- [ ] Chat takes full width
- [ ] Right sidebar NOT visible (hidden by CSS)
- [ ] Hamburger menu functional

**Mobile (375x667)**
- [ ] Left sidebar hidden by default
- [ ] Chat full width
- [ ] Hamburger menu works
- [ ] Input form accessible
- [ ] No horizontal scroll

### Functionality Testing

#### Chat Operations
- [ ] Create new chat - sidebar updates
- [ ] Upload PDF - appears in right sidebar
- [ ] Send message - loading spinner positioned correctly
- [ ] Delete chat - removes from sidebar
- [ ] Rename chat - title updates immediately
- [ ] Search in admin dashboard - filters users correctly

#### Admin Operations
- [ ] View admin dashboard
- [ ] See all users listed
- [ ] Click user - expands to show sessions
- [ ] Click eye icon - modal opens with chat data
- [ ] Modal displays all messages correctly
- [ ] Modal displays all attachments correctly
- [ ] Download attachment from modal - works
- [ ] Delete chat from dashboard - works
- [ ] Delete user - cascades deletion of chats

#### File Operations
- [ ] Upload PDF - Cloudinary upload succeeds
- [ ] Pinecone indexing completes
- [ ] Attachment appears in sidebar immediately
- [ ] Can send RAG queries with attachment context
- [ ] Delete chat - Cloudinary file deleted
- [ ] Delete document - file properly cleaned up

### Error Handling
- [ ] Upload non-PDF file - shows error message
- [ ] Upload file > 10MB - shows error message
- [ ] Network error during upload - graceful handling
- [ ] Delete without confirmation - prevents accidental deletion
- [ ] Admin access without permission - redirects properly

### Performance Metrics
- [ ] Modal opens within 1 second
- [ ] Chat loads within 2 seconds
- [ ] Attachment list loads immediately
- [ ] File uploads show progress
- [ ] No console errors on load
- [ ] No memory leaks with repeated modal opens

## Post-Deployment Monitoring

### Logs to Monitor
- [ ] Check `debug.log` for errors
- [ ] Monitor Django error logs
- [ ] Check browser console for JS errors
- [ ] Monitor Pinecone API calls
- [ ] Monitor Cloudinary uploads

### Metrics to Track
- [ ] Modal load times
- [ ] File upload success rate
- [ ] Admin dashboard usage
- [ ] Attachment download frequency
- [ ] Error rates in API endpoint

## Rollback Procedures

If critical issues found:

1. **Database**: No migrations required (backward compatible)
2. **Templates**: Restore `index.html`, `dashboard.html`, `user_list.html`
3. **Code**: Remove new API endpoint from `views.py` and `urls.py`
4. **Docs**: Revert naming changes
5. **Clear Cache**: `python manage.py clear_cache` (if applicable)

## Sign-Off Checklist

- [ ] All tests passed
- [ ] No console errors
- [ ] No server errors
- [ ] Admin team approves changes
- [ ] Documentation updated
- [ ] Team trained on new features
- [ ] Monitoring configured
- [ ] Backup confirmed before deploy

## Notes for Testers

### What's New
1. **Right Sidebar**: Attachments now have dedicated space
2. **Modal Overlay**: Admin chat viewing is now inline
3. **Loading Indicator**: Fixed positioning for visibility
4. **Naming**: "God Mode" renamed to "Nexus Core"

### Known Considerations
- Attachments sidebar hidden on mobile (intentional responsive design)
- Modal requires JavaScript enabled
- API endpoint requires staff authentication
- Attachment display depends on Cloudinary URL validity

### Troubleshooting

**Problem**: Attachments sidebar not visible
- **Solution**: Check viewport width (must be 1024px+), Clear browser cache

**Problem**: Modal won't open
- **Solution**: Check browser console for errors, Verify user is superuser

**Problem**: Loading spinner in wrong position
- **Solution**: Hard refresh (Ctrl+Shift+R), Check CSS file loaded

**Problem**: API endpoint returns 404
- **Solution**: Verify session ID exists, Check user is staff member

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Sign-Off**: _____________

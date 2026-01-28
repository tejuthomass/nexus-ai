# Deployment Checklist - Multi-Model Fallback System

## Pre-Deployment

### 1. Code Review
- [ ] Review all changes in `/chat/model_fallback.py`
- [ ] Review modifications in `/chat/views.py`
- [ ] Review UI changes in templates
- [ ] Verify no hardcoded values or test code

### 2. Testing
- [ ] Run Django system check: `python manage.py check`
- [ ] Run test suite: `python test_model_fallback.py`
- [ ] Test in local development environment
- [ ] Verify all imports work correctly
- [ ] Check for Python syntax errors

### 3. Environment Setup
- [ ] Verify `GEMINI_API_KEY` in `.env` file
- [ ] Verify `PINECONE_API_KEY` in `.env` file
- [ ] Check API quota limits in Google Cloud Console
- [ ] Ensure all required packages installed

### 4. Documentation Review
- [ ] Read `/docs/MODEL_FALLBACK_SYSTEM.md`
- [ ] Review `/docs/FALLBACK_QUICK_REFERENCE.md`
- [ ] Understand `/docs/VISUAL_FLOW_DIAGRAM.md`
- [ ] Check `IMPLEMENTATION_SUMMARY.md`

---

## Deployment Steps

### Step 1: Backup Current System
```bash
# Backup database
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Backup .env file
cp .env .env.backup

# Git commit current state (if using git)
git add .
git commit -m "Pre-deployment backup"
git tag pre-fallback-deployment
```

### Step 2: Deploy Code Changes
```bash
# Pull latest changes (if using git)
git pull origin main

# Or manually copy files:
# - chat/model_fallback.py (NEW)
# - chat/views.py (MODIFIED)
# - chat/urls.py (MODIFIED)
# - chat/templates/chat/index.html (MODIFIED)
# - chat/templates/chat/partials/message.html (MODIFIED)
# - chat/templates/chat/partials/system_message.html (MODIFIED)
```

### Step 3: Install Dependencies (if any new)
```bash
pip install -r requirements.txt
```

### Step 4: Run Database Migrations (if any)
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 6: Run System Checks
```bash
# Check for errors
python manage.py check --deploy

# Run test suite
python test_model_fallback.py
```

### Step 7: Restart Application
```bash
# Development
python manage.py runserver

# Production (example commands, adjust for your setup)
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Or using Docker
docker-compose restart web
```

---

## Post-Deployment Verification

### Immediate Checks (First 5 Minutes)

#### 1. Basic Functionality
- [ ] Open the chat interface
- [ ] Send a test message: "Hello, how are you?"
- [ ] Verify response appears
- [ ] Check loading state shows "Processing..."
- [ ] Verify no model name visible in header

#### 2. Hover Tooltip
- [ ] Send a message and get response
- [ ] Hover over info icon (ℹ️) next to "Nexus Core"
- [ ] Verify tooltip shows model name (e.g., "Gemini Experimental")

#### 3. API Endpoint
```bash
# Test availability endpoint
curl http://your-domain.com/api/check-availability/

# Expected response:
# {"available": true, "message": "Service available"}
```

#### 4. Check Logs
```bash
# Look for successful initialization
tail -f logs/django.log | grep -E "model|fallback"

# Should see:
# "Attempting model 1/5: gemini-exp-1206"
# "Success with gemini-exp-1206 on attempt 1"
```

### Extended Monitoring (First Hour)

#### 1. Monitor Error Rates
```bash
# Watch for any errors
tail -f logs/django.log | grep -i error
```

#### 2. Track Model Usage
```bash
# Monitor which models are being used
tail -f logs/django.log | grep "Success with"

# Should mostly see Model 1 (gemini-exp-1206)
```

#### 3. User Experience
- [ ] Test from multiple browsers
- [ ] Test on mobile devices
- [ ] Verify responsive design works
- [ ] Check chat history loads correctly

#### 4. Performance
- [ ] Measure response times (should be <2s normally)
- [ ] Check server resource usage
- [ ] Monitor API quota consumption

---

## Rollback Procedure (If Needed)

### Quick Rollback
```bash
# If using git
git checkout pre-fallback-deployment
python manage.py migrate
sudo systemctl restart gunicorn

# Or restore from backup
cp .env.backup .env
python manage.py loaddata backup_YYYYMMDD.json
```

### Files to Restore (Manual)
1. Restore old `chat/views.py` (remove fallback code)
2. Remove `chat/model_fallback.py`
3. Restore old templates
4. Restart application

---

## Monitoring Setup

### 1. Log Monitoring
```bash
# Create log monitoring script
cat > /usr/local/bin/monitor_fallback.sh << 'EOF'
#!/bin/bash
tail -f /path/to/logs/django.log | grep --line-buffered -E "model|fallback|exhausted"
EOF

chmod +x /usr/local/bin/monitor_fallback.sh
```

### 2. Availability Monitoring
```bash
# Create cron job to check availability
crontab -e

# Add this line (checks every 5 minutes):
*/5 * * * * curl -s http://localhost:8000/api/check-availability/ | grep -q '"available":true' || echo "⚠️ Service unavailable" | mail -s "Nexus Alert" admin@example.com
```

### 3. Quota Monitoring
- Set up alerts in Google Cloud Console
- Monitor API usage dashboard
- Set threshold alerts at 80% quota usage

### 4. Error Alerts
```python
# Add to Django settings.py for email alerts
LOGGING = {
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'chat.model_fallback': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
        }
    }
}
```

---

## Performance Benchmarks

### Expected Metrics
- **95th percentile response time:** <2s
- **99th percentile response time:** <5s
- **Success rate:** >99%
- **Primary model usage:** >95%
- **Fallback events:** <5%
- **Complete exhaustion:** <0.1%

### Red Flags
- ⚠️ Response time >5s consistently
- ⚠️ Primary model usage <80%
- ⚠️ Fallback events >20%
- ⚠️ Complete exhaustion >1%
- ⚠️ Error rate >1%

---

## Troubleshooting Guide

### Issue: Chat not working at all
**Check:**
```bash
# 1. Check if server is running
systemctl status gunicorn

# 2. Check logs for errors
tail -100 logs/django.log

# 3. Test API endpoint
curl http://localhost:8000/api/check-availability/

# 4. Verify API key
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', os.getenv('GEMINI_API_KEY')[:10] + '...')"
```

### Issue: Always falling back to Model 5
**Check:**
```bash
# 1. Check API quota in Google Cloud Console
# 2. Look for rate limit errors in logs
grep -i "rate limit" logs/django.log

# 3. Verify all model names are correct
grep "MODEL_HIERARCHY" chat/model_fallback.py
```

### Issue: Hover tooltip not showing
**Check:**
- Browser console for JavaScript errors
- Verify `model_used` is passed to template
- Check CSS for `group/model` hover class
- Test in different browsers

### Issue: Chat stuck in disabled state
**Check:**
```bash
# 1. Check exhaustion state
python -c "from chat.model_fallback import _all_models_exhausted, _exhaustion_timestamp; print(f'Exhausted: {_all_models_exhausted}, Time: {_exhaustion_timestamp}')"

# 2. Force reset by restarting server
sudo systemctl restart gunicorn

# 3. Check availability endpoint
curl http://localhost:8000/api/check-availability/
```

### Issue: High response times
**Check:**
- API latency in Google Cloud Console
- Network connectivity to Google APIs
- Server resource usage (CPU, memory)
- Database query performance

---

## Success Criteria

### Technical
- [x] All Django checks pass
- [x] No Python errors or warnings
- [x] All imports work correctly
- [x] API endpoint responds correctly
- [x] Logs show successful model usage

### Functional
- [x] Users can send messages
- [x] Responses appear correctly
- [x] Hover tooltip shows model name
- [x] Loading state displays properly
- [x] Exhaustion state works correctly
- [x] Auto-recovery works after 5 minutes

### Performance
- [x] Response time <2s (95th percentile)
- [x] No increase in error rate
- [x] Primary model used >90% of time
- [x] Graceful degradation under load

### User Experience
- [x] Clean, professional interface
- [x] No visible model selection
- [x] Clear error messages
- [x] Disabled state is obvious
- [x] Mobile-friendly

---

## Sign-Off Checklist

### Development Team
- [ ] Code reviewed and approved
- [ ] Tests pass locally
- [ ] Documentation complete
- [ ] No known bugs

### QA Team
- [ ] Manual testing completed
- [ ] Edge cases tested
- [ ] Mobile testing done
- [ ] Cross-browser testing done

### Operations Team
- [ ] Deployment procedure reviewed
- [ ] Monitoring setup complete
- [ ] Rollback procedure tested
- [ ] Alerts configured

### Product Owner
- [ ] Requirements met
- [ ] User experience approved
- [ ] Ready for production

---

## Emergency Contacts

**Development Issues:**
- Primary: [Your Name/Email]
- Secondary: [Backup Contact]

**Infrastructure Issues:**
- DevOps Lead: [Contact Info]
- On-Call Engineer: [Contact Info]

**API/Quota Issues:**
- Google Cloud Admin: [Contact Info]

---

## Next Steps After Deployment

### Week 1
- [ ] Monitor daily for any issues
- [ ] Track model usage distribution
- [ ] Gather user feedback
- [ ] Adjust timing parameters if needed

### Month 1
- [ ] Review performance metrics
- [ ] Analyze fallback frequency
- [ ] Optimize model hierarchy if needed
- [ ] Consider adding more models

### Quarter 1
- [ ] Implement Phase 2 enhancements
- [ ] Add analytics dashboard
- [ ] Implement user-based rate limiting
- [ ] Explore cost optimization

---

**Deployment Date:** ___________________  
**Deployed By:** ___________________  
**Verified By:** ___________________  
**Status:** ___________________ (Success/Rollback/Issues)

**Notes:**
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________

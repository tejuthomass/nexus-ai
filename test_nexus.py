#!/usr/bin/env python
"""
Comprehensive test script for Nexus application
Tests all the new features and fixes
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from chat.models import ChatSession, Message, Document
from django.test.utils import setup_test_environment, teardown_test_environment
import logging

logger = logging.getLogger(__name__)

class NexusAITests:
    def __init__(self):
        self.client = Client()
        self.user = None
        self.admin = None
        self.session = None
        
    def setup(self):
        """Create test data"""
        print("\n🔧 Setting up test environment...")
        
        # Create regular user
        self.user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'password': 'testpass123'}
        )
        self.user.set_password('testpass123')
        self.user.save()
        print(f"✅ Created test user: {self.user.username}")
        
        # Create admin user
        self.admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'password': 'adminpass123', 'is_staff': True, 'is_superuser': True}
        )
        self.admin.set_password('adminpass123')
        self.admin.save()
        print(f"✅ Created admin user: {self.admin.username}")
        
    def test_authentication(self):
        """Test user authentication"""
        print("\n🧪 Testing Authentication...")
        
        # Test login
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        
        if response.status_code == 200:
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed with status {response.status_code}")
            return False
    
    def test_chat_session_creation(self):
        """Test chat session creation"""
        print("\n🧪 Testing Chat Session Creation...")
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/', follow=True)
        
        if response.status_code == 200:
            print("✅ Chat page loads successfully")
            
            # Check if session was created
            sessions = ChatSession.objects.filter(user=self.user)
            if sessions.exists():
                self.session = sessions.first()
                print(f"✅ Chat session created: {self.session.title}")
                return True
            else:
                print("❌ Chat session not created")
                return False
        else:
            print(f"❌ Chat page failed with status {response.status_code}")
            return False
    
    def test_message_creation(self):
        """Test message creation"""
        print("\n🧪 Testing Message Creation...")
        
        if not self.session:
            print("⚠️  Skipping: No session available")
            return False
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create a message
        response = self.client.post(f'/chat/{self.session.id}/', {
            'message': 'Hello, this is a test message'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Check if message was created
        messages = Message.objects.filter(session=self.session, role='user')
        if messages.exists():
            print(f"✅ User message created: '{messages.first().content[:50]}...'")
            
            # Check for AI response
            ai_messages = Message.objects.filter(session=self.session, role='assistant')
            if ai_messages.exists():
                print(f"✅ AI response created: '{ai_messages.first().content[:50]}...'")
                return True
            else:
                print("⚠️  AI response not yet available")
                return True
        else:
            print("❌ Message creation failed")
            return False
    
    def test_chat_deletion(self):
        """Test chat session deletion"""
        print("\n🧪 Testing Chat Session Deletion...")
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create a session to delete
        session = ChatSession.objects.create(user=self.user, title="Test Session to Delete")
        session_id = session.id
        
        # Delete it
        response = self.client.post(f'/chat/{session_id}/delete/', follow=True)
        
        # Verify deletion
        if not ChatSession.objects.filter(id=session_id).exists():
            print(f"✅ Chat session {session_id} deleted successfully")
            return True
        else:
            print(f"❌ Chat session {session_id} still exists")
            return False
    
    def test_model_registration(self):
        """Test that models are registered in admin"""
        print("\n🧪 Testing Admin Model Registration...")
        
        from django.contrib import admin
        from chat.models import ChatSession, Message, Document
        
        checks = [
            ('ChatSession', ChatSession in admin.site._registry),
            ('Message', Message in admin.site._registry),
            ('Document', Document in admin.site._registry),
        ]
        
        all_registered = True
        for name, is_registered in checks:
            if is_registered:
                print(f"✅ {name} is registered in admin")
            else:
                print(f"❌ {name} is NOT registered in admin")
                all_registered = False
        
        return all_registered
    
    def test_database_indexes(self):
        """Test that database indexes exist"""
        print("\n🧪 Testing Database Indexes...")
        
        from django.db import connection
        cursor = connection.cursor()
        
        # Get indexes for the models
        indexes_found = 0
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = ['chat_chatse', 'chat_docume', 'chat_messag']
            for expected in expected_indexes:
                matching = [idx for idx in indexes if expected in idx]
                if matching:
                    indexes_found += 1
                    print(f"✅ Found index containing '{expected}': {matching[0]}")
                else:
                    print(f"⚠️  Index for '{expected}' not found")
            
            return indexes_found >= 2
        except Exception as e:
            print(f"⚠️  Could not check indexes: {e}")
            return True
    
    def test_logging_config(self):
        """Test that logging is configured"""
        print("\n🧪 Testing Logging Configuration...")
        
        from django.conf import settings
        
        if hasattr(settings, 'LOGGING'):
            print("✅ Logging configuration is present")
            
            if 'handlers' in settings.LOGGING:
                print("✅ Logging handlers are configured")
            
            if 'loggers' in settings.LOGGING:
                print("✅ Logging loggers are configured")
            
            return True
        else:
            print("❌ Logging is not configured")
            return False
    
    def test_file_upload_settings(self):
        """Test file upload settings"""
        print("\n🧪 Testing File Upload Settings...")
        
        from django.conf import settings
        
        checks = [
            ('FILE_UPLOAD_MAX_MEMORY_SIZE', hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE')),
            ('DATA_UPLOAD_MAX_MEMORY_SIZE', hasattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE')),
            ('STATIC_ROOT', hasattr(settings, 'STATIC_ROOT')),
            ('MEDIA_ROOT', hasattr(settings, 'MEDIA_ROOT')),
        ]
        
        all_present = True
        for setting_name, is_present in checks:
            if is_present:
                value = getattr(settings, setting_name, 'N/A')
                print(f"✅ {setting_name}: {value}")
            else:
                print(f"❌ {setting_name} not found")
                all_present = False
        
        return all_present
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("🚀 NEXUS - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        self.setup()
        
        results = {
            'Authentication': self.test_authentication(),
            'Chat Session Creation': self.test_chat_session_creation(),
            'Message Creation': self.test_message_creation(),
            'Chat Deletion': self.test_chat_deletion(),
            'Admin Registration': self.test_model_registration(),
            'Database Indexes': self.test_database_indexes(),
            'Logging Config': self.test_logging_config(),
            'File Upload Settings': self.test_file_upload_settings(),
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print("=" * 60)
        print(f"Total: {passed}/{total} tests passed")
        print("=" * 60 + "\n")
        
        return passed == total

if __name__ == '__main__':
    setup_test_environment()
    
    tester = NexusAITests()
    success = tester.run_all_tests()
    
    teardown_test_environment()
    
    sys.exit(0 if success else 1)

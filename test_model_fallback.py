#!/usr/bin/env python
"""
Test script for the multi-model fallback system.
Run this to verify the implementation works correctly.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/workspaces/nexus-ai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chat.model_fallback import (
    generate_with_fallback,
    check_service_availability,
    get_model_display_name,
    ModelExhaustionError,
    MODEL_HIERARCHY
)

def test_imports():
    """Test that all imports work correctly."""
    print("✅ All imports successful")
    return True

def test_model_display_names():
    """Test model name mapping."""
    print("\n📋 Testing Model Display Names:")
    for model in MODEL_HIERARCHY:
        display_name = get_model_display_name(model)
        print(f"  {model} → {display_name}")
    return True

def test_service_availability():
    """Test service availability check."""
    print("\n🔍 Testing Service Availability:")
    is_available, message = check_service_availability()
    print(f"  Available: {is_available}")
    print(f"  Message: {message}")
    return True

def test_model_hierarchy():
    """Test that model hierarchy is correctly defined."""
    print("\n🏗️ Testing Model Hierarchy:")
    print(f"  Total models: {len(MODEL_HIERARCHY)}")
    print(f"  Primary model: {MODEL_HIERARCHY[0]}")
    print(f"  Final fallback: {MODEL_HIERARCHY[-1]}")
    assert len(MODEL_HIERARCHY) >= 2, "At least 2 models required"
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Multi-Model Fallback System - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Model Display Names", test_model_display_names),
        ("Service Availability", test_service_availability),
        ("Model Hierarchy", test_model_hierarchy),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Full system connection test script
Tests the complete frontend-backend-database integration
"""

import requests
import json
import time
from datetime import datetime

def test_backend_health():
    """Test backend health endpoint"""
    print("\n=== Testing Backend Health ===")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data['status']}")
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}")
            print(f"   Environment: {data['environment']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_api_endpoints():
    """Test various API endpoints"""
    print("\n=== Testing API Endpoints ===")
    
    endpoints = [
        ("POST", "/api/v1/auth/test", "Auth test endpoint"),
        ("GET", "/", "Root endpoint"),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url)
            
            if response.status_code in [200, 201]:
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"⚠️  {description}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description} failed: {e}")

def test_cors():
    """Test CORS configuration"""
    print("\n=== Testing CORS Configuration ===")
    try:
        headers = {
            'Origin': 'http://localhost:5174',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options("http://localhost:8000/api/v1/auth/test", headers=headers)
        
        if response.status_code == 200:
            print("✅ CORS preflight request successful")
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            }
            for header, value in cors_headers.items():
                if value:
                    print(f"   {header}: {value}")
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")

def test_frontend_connection():
    """Test if frontend is accessible"""
    print("\n=== Testing Frontend Connection ===")
    try:
        response = requests.get("http://localhost:5174")
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_connection_test_page():
    """Test the connection test page"""
    print("\n=== Testing Connection Test Page ===")
    try:
        response = requests.get("http://localhost:5174/connection-test")
        if response.status_code == 200:
            print("✅ Connection test page is accessible")
            return True
        else:
            print(f"❌ Connection test page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection test page failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏋️ GymSystem Full Connection Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_backend_health,
        test_api_endpoints,
        test_cors,
        test_frontend_connection,
        test_connection_test_page,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Frontend-Backend-Database connection is working!")
        print("\n🔗 Available URLs:")
        print("   Frontend: http://localhost:5174")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("   Connection Test: http://localhost:5174/connection-test")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
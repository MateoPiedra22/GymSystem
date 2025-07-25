#!/usr/bin/env python3

import requests
import json

def test_debug_endpoints():
    """Test the debug endpoints to isolate API issues"""
    
    base_url = "http://localhost:8000/api/v1/auth"
    
    print("Testing debug endpoints...")
    
    # Test 1: Simple test endpoint
    print("\n1. Testing /test endpoint...")
    try:
        response = requests.post(f"{base_url}/test")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Login simple endpoint
    print("\n2. Testing /login-simple endpoint...")
    try:
        data = {
            "email": "test@example.com",
            "password": "password"
        }
        response = requests.post(f"{base_url}/login-simple", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Login debug endpoint
    print("\n3. Testing /login-debug endpoint...")
    try:
        data = {
            "email": "test@example.com",
            "password": "password"
        }
        response = requests.post(f"{base_url}/login-debug", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Main login endpoint
    print("\n4. Testing /login endpoint...")
    try:
        data = {
            "email": "test@example.com",
            "password": "password"
        }
        response = requests.post(f"{base_url}/login", json=data)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_debug_endpoints()
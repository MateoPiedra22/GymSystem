#!/usr/bin/env python3
"""
Test script to verify login functionality
"""

import requests
import json

def test_login():
    """Test the login endpoint"""
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test data
    login_data = {
        "email": "test@example.com",
        "password": "password"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Testing login endpoint...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(login_data, indent=2)}")
        
        response = requests.post(url, json=login_data, headers=headers)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Login failed!")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - backend server might not be running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_login()
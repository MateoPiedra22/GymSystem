#!/usr/bin/env python3
"""
Direct test of login API to debug the authentication issue
"""

import requests
import json

def test_login():
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test data - using the existing test user
    login_data = {
        "email": "test@example.com",
        "password": "password"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"Testing login at: {url}")
    print(f"Login data: {json.dumps(login_data, indent=2)}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=login_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nLogin successful!")
            print(f"Access Token: {data.get('access_token', 'Not found')[:50]}...")
            print(f"Refresh Token: {data.get('refresh_token', 'Not found')[:50]}...")
            print(f"User: {data.get('user', 'Not found')}")
        else:
            print(f"\nLogin failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error response: {response.text}")
                
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(f"Exception type: {type(e).__name__}")

if __name__ == "__main__":
    test_login()
#!/usr/bin/env python3
"""
Test script to verify login functionality after refresh token fix
"""

import requests
import json

def test_login():
    """Test login endpoint with correct credentials"""
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test credentials
    credentials = {
        "email": "test@example.com",
        "password": "password"
    }
    
    try:
        print("Testing login endpoint...")
        response = requests.post(url, json=credentials)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Login SUCCESS!")
            print(f"Response data keys: {list(data.keys())}")
            
            # Check for required fields
            required_fields = ['access_token', 'refresh_token', 'token_type', 'expires_in', 'user']
            for field in required_fields:
                if field in data:
                    print(f"✅ {field}: Present")
                    if field == 'access_token':
                        print(f"   Value: {data[field][:50]}...")
                    elif field == 'refresh_token':
                        print(f"   Value: {data[field][:50]}...")
                    elif field == 'user':
                        print(f"   User ID: {data[field].get('id')}")
                        print(f"   User Email: {data[field].get('email')}")
                    else:
                        print(f"   Value: {data[field]}")
                else:
                    print(f"❌ {field}: Missing")
            
            return True
        else:
            print(f"\n❌ Login FAILED!")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    if success:
        print("\n🎉 Login test completed successfully!")
    else:
        print("\n💥 Login test failed!")
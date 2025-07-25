#!/usr/bin/env python3
import requests
import json

def test_login():
    url = "http://localhost:8000/api/v1/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("Login SUCCESS!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print("Login FAILED!")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
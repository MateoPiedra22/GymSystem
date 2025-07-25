import requests
import json

def test_login_detailed():
    url = "http://localhost:8000/api/v1/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password"
    }
    
    print("Testing login endpoint with detailed error capture...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=data)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Try to get JSON response
        try:
            json_response = response.json()
            print(f"JSON Response: {json.dumps(json_response, indent=2)}")
        except:
            print(f"Raw Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
        else:
            print("❌ Login failed!")
            
    except Exception as e:
        print(f"❌ Request failed with exception: {e}")

if __name__ == "__main__":
    test_login_detailed()
#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.core.auth import auth_manager
from app.models.user import User
from app.api.auth import create_user_tokens
from datetime import datetime

def test_direct_login():
    """Test login functionality directly without API"""
    
    print("Testing direct login functionality...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test authentication
        print("1. Testing authentication...")
        user = auth_manager.authenticate_user(db, "test@example.com", "password")
        
        if not user:
            print("❌ Authentication failed")
            return False
            
        print(f"✅ Authentication successful: {user.email}")
        
        # Check if user is active
        print("2. Checking user status...")
        if not user.is_active:
            print("❌ User is not active")
            return False
            
        print(f"✅ User is active: {user.is_active}")
        
        # Update last login
        print("3. Updating login info...")
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.commit()
        print(f"✅ Login info updated. Count: {user.login_count}")
        
        # Create tokens
        print("4. Creating tokens...")
        tokens = create_user_tokens(user)
        print(f"✅ Tokens created: {bool(tokens)}")
        
        if tokens:
            print(f"   Access token: {tokens['access_token'][:50]}...")
            print(f"   Token type: {tokens['token_type']}")
            print(f"   Expires in: {tokens['expires_in']} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during direct login test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_direct_login()
    if success:
        print("\n🎉 Direct login test PASSED!")
    else:
        print("\n💥 Direct login test FAILED!")
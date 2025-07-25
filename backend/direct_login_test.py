#!/usr/bin/env python3
"""
Direct login test to bypass potential middleware issues
"""

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.auth import auth_manager, create_user_tokens
from datetime import datetime

def test_direct_login():
    """Test login logic directly"""
    
    # Get database session
    db = next(get_db())
    
    try:
        print("=== Direct Login Test ===")
        
        # Test credentials
        email = "test@example.com"
        password = "password"
        
        print(f"1. Testing authentication for: {email}")
        
        # Authenticate user directly
        user = auth_manager.authenticate_user(db, email, password)
        
        if not user:
            print("❌ Authentication failed")
            return False
        
        print(f"✅ User authenticated: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"   Active: {user.is_active}")
        print(f"   Login count: {user.login_count}")
        
        # Check if user is active
        if not user.is_active:
            print("❌ User is not active")
            return False
        
        print("✅ User is active")
        
        # Update last login
        print("2. Updating login info...")
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.commit()
        print(f"✅ Login count updated to: {user.login_count}")
        
        # Create tokens
        print("3. Creating tokens...")
        try:
            tokens = create_user_tokens(user)
            print("✅ Tokens created successfully")
            print(f"   Access token: {tokens['access_token'][:50]}...")
            print(f"   Token type: {tokens['token_type']}")
            print(f"   Expires in: {tokens['expires_in']} seconds")
            return True
        except Exception as e:
            print(f"❌ Token creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Direct login test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_direct_login()
    if success:
        print("\n🎉 Direct login test PASSED")
    else:
        print("\n💥 Direct login test FAILED")
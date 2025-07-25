#!/usr/bin/env python3
"""
Script to test authentication directly
"""

from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import auth_manager

def test_authentication():
    """Test authentication process step by step"""
    
    # Get database session
    db = SessionLocal()
    
    try:
        email = "test@example.com"
        password = "password"
        
        print(f"Testing authentication for: {email}")
        
        # Step 1: Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("❌ User not found")
            return
        
        print(f"✅ User found: {user.email}")
        print(f"   Active: {user.is_active}")
        print(f"   Role: {user.role}")
        
        # Step 2: Test password verification
        print(f"\nTesting password verification...")
        print(f"Password hash: {user.password_hash[:30]}...")
        
        is_valid = auth_manager.verify_password(password, user.password_hash)
        print(f"Password valid: {is_valid}")
        
        # Step 3: Test full authentication
        print(f"\nTesting full authentication...")
        auth_result = auth_manager.authenticate_user(db, email, password)
        
        if auth_result:
            print(f"✅ Authentication successful: {auth_result.email}")
        else:
            print("❌ Authentication failed")
            
        # Step 4: Test with wrong password
        print(f"\nTesting with wrong password...")
        wrong_auth = auth_manager.authenticate_user(db, email, "wrongpassword")
        if wrong_auth:
            print("❌ Wrong password accepted (this is bad!)")
        else:
            print("✅ Wrong password correctly rejected")
            
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_authentication()
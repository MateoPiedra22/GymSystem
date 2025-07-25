#!/usr/bin/env python3
"""
Script to verify user data and password hash
"""

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.auth import auth_manager

def verify_user():
    """Verify user exists and password is correct"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find the test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not user:
            print("❌ User not found in database")
            return False
        
        print(f"✅ User found: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Active: {user.is_active}")
        print(f"   Login count: {user.login_count}")
        print(f"   Password hash: {user.password_hash[:50]}...")
        
        # Test password verification
        test_password = "password"
        is_valid = auth_manager.verify_password(test_password, user.password_hash)
        
        if is_valid:
            print(f"✅ Password verification successful")
        else:
            print(f"❌ Password verification failed")
            
            # Try to create a new hash and compare
            new_hash = auth_manager.get_password_hash(test_password)
            print(f"   New hash would be: {new_hash[:50]}...")
            
            # Test with new hash
            is_new_valid = auth_manager.verify_password(test_password, new_hash)
            print(f"   New hash verification: {is_new_valid}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    verify_user()
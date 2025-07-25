#!/usr/bin/env python3
"""
Simple authentication test without verbose logging
"""

import logging
# Disable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import auth_manager

def test_auth():
    """Test authentication"""
    
    db = SessionLocal()
    
    try:
        email = "test@example.com"
        password = "password"
        
        print(f"Testing: {email} / {password}")
        
        # Test authentication
        user = auth_manager.authenticate_user(db, email, password)
        
        if user:
            print(f"✅ SUCCESS: {user.email} authenticated")
            print(f"   Active: {user.is_active}")
            print(f"   Role: {user.role}")
        else:
            print("❌ FAILED: Authentication failed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_auth()
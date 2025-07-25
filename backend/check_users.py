#!/usr/bin/env python3
"""
Script to check users in database
"""

from app.core.database import SessionLocal
from app.models.user import User

def check_users():
    """Check users in database"""
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        print(f"Total users: {len(users)}")
        
        for user in users:
            print(f"User: {user.email}, Active: {user.is_active}, Role: {user.role}")
            
        # Check for test user specifically
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            print(f"\nTest user found: {test_user.email}")
            print(f"Password hash: {test_user.password_hash[:20]}...")
        else:
            print("\nTest user not found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
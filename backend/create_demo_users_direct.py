#!/usr/bin/env python3
"""
Simple Demo User Creation Script - Direct database insertion
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.core.database import get_database_session, init_database
from app.core.models import User, UserRole
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def create_demo_users_direct():
    """Create demo users directly in database"""
    
    # Initialize database first
    logger.info("Initializing database...")
    init_database()
    
    # Get database session
    db_gen = get_database_session()
    db: Session = next(db_gen)
    
    try:
        # Check if users already exist
        existing_admin = db.query(User).filter(User.email == "admin@demo.com").first()
        existing_user = db.query(User).filter(User.email == "user@demo.com").first()
        
        if existing_admin:
            logger.info("Admin user already exists")
        else:
            # Create admin user directly
            admin_user = User(
                email="admin@demo.com",
                username="admin",
                hashed_password=pwd_context.hash("admin123"),
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            logger.info("Created admin user: admin@demo.com")
        
        if existing_user:
            logger.info("Demo user already exists")
        else:
            # Create regular user directly
            demo_user = User(
                email="user@demo.com",
                username="sarah_johnson",
                hashed_password=pwd_context.hash("user123"),
                first_name="Sarah",
                last_name="Johnson",
                role=UserRole.USER,
                is_active=True
            )
            db.add(demo_user)
            logger.info("Created demo user: user@demo.com")
        
        db.commit()
        logger.info("✅ Demo users created successfully!")
        
        # Verify users were created
        admin_check = db.query(User).filter(User.email == "admin@demo.com").first()
        user_check = db.query(User).filter(User.email == "user@demo.com").first()
        
        print("\n" + "="*50)
        print("DEMO USER CREATION RESULTS")
        print("="*50)
        print(f"Admin user created: {admin_check is not None}")
        print(f"Regular user created: {user_check is not None}")
        print()
        print("DEMO USER CREDENTIALS")
        print("="*50)
        print("Admin User:")
        print("  Email: admin@demo.com")
        print("  Password: admin123")
        print()
        print("Regular User:")
        print("  Email: user@demo.com") 
        print("  Password: user123")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error creating demo users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_users_direct()
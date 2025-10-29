#!/usr/bin/env python3
"""
Demo User Creation Script
Creates demo admin and user accounts for testing
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.core.database import get_database_session, init_database
from app.core.security import auth_service
from app.core.models import UserRole
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_users():
    """Create demo users for testing"""
    
    # Initialize database first
    logger.info("Initializing database...")
    init_database()
    
    # Get database session
    db_gen = get_database_session()
    db: Session = next(db_gen)
    
    try:
        # Demo admin user
        admin_data = {
            "email": "admin@demo.com",
            "username": "admin",
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "User",
            "role": UserRole.ADMIN,
            "is_active": True
        }
        
        # Demo regular user
        user_data = {
            "email": "user@demo.com", 
            "username": "sarah_johnson",
            "password": "user123",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": UserRole.USER,
            "is_active": True
        }
        
        # Check if users already exist
        existing_admin = auth_service.get_user_by_email_or_username(db, "admin@demo.com")
        existing_user = auth_service.get_user_by_email_or_username(db, "user@demo.com")
        
        if existing_admin:
            logger.info("Admin user already exists")
        else:
            try:
                admin_user = auth_service.create_user(db, admin_data)
                logger.info(f"Created admin user: {admin_user.email}")
            except Exception as e:
                logger.error(f"Error creating admin user: {e}")
                print(f"Admin creation error details: {e}")
        
        if existing_user:
            logger.info("Demo user already exists")
        else:
            try:
                demo_user = auth_service.create_user(db, user_data)
                logger.info(f"Created demo user: {demo_user.email}")
            except Exception as e:
                logger.error(f"Error creating demo user: {e}")
                print(f"User creation error details: {e}")
        
        db.commit()
        logger.info("✅ Demo users created successfully!")
        
        print("\n" + "="*50)
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
    create_demo_users()
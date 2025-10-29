#!/usr/bin/env python3
"""
Initialize the database with all required tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_database

if __name__ == "__main__":
    print("🗄️ Initializing database...")
    
    success = init_database()
    
    if success:
        print("✅ Database tables created successfully!")
    else:
        print("❌ Failed to create database tables")
        sys.exit(1)
#!/usr/bin/env python3
"""
Startup script for Flogenix backend
Handles proper CORS configuration and error reporting
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting Flogenix Backend Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Auto-reload enabled for development")
    print("🌐 CORS configured for ports: 5173, 3000, 4173, 8080, 8081")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("Make sure port 8000 is not already in use")
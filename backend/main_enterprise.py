"""
Flogenix Enterprise Backend - Main Application
FastAPI application with enterprise authentication, multi-agent AI, and async processing
"""

import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn
import logging

# Import enterprise components
from app.core.config import get_settings, is_production
from app.core.database import init_database, get_database_session
from app.core.security import auth_service, log_audit_event, AuditAction, get_current_user
from app.core.models import User
from app.core.openapi_config import custom_openapi

# Import API routers
from app.api.claims import router as legacy_claims_router
from app.api.enterprise_claims import router as enterprise_claims_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router

# Import services
from app.services.celery_tasks import celery_app

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.logging.level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_demo_users_if_needed():
    """Create demo users if they don't exist"""
    try:
        from app.core.database import get_database_session
        from app.core.models import UserRole
        
        # Get database session
        db_gen = get_database_session()
        db = next(db_gen)
        
        try:
            # Check if admin user exists
            existing_admin = auth_service.get_user_by_email(db, "admin@demo.com")
            if not existing_admin:
                admin_data = {
                    "email": "admin@demo.com",
                    "username": "admin",
                    "password": "admin123",
                    "first_name": "Admin",
                    "last_name": "User",
                    "role": UserRole.ADMIN,
                    "is_active": True
                }
                auth_service.create_user(db, admin_data)
                logger.info("Created demo admin user: admin@demo.com")
            
            # Check if regular user exists
            existing_user = auth_service.get_user_by_email(db, "user@demo.com")
            if not existing_user:
                user_data = {
                    "email": "user@demo.com",
                    "username": "sarah_johnson", 
                    "password": "user123",
                    "first_name": "Sarah",
                    "last_name": "Johnson",
                    "role": UserRole.USER,
                    "is_active": True
                }
                auth_service.create_user(db, user_data)
                logger.info("Created demo user: user@demo.com")
                
            db.commit()
            logger.info("Demo users initialized successfully")
            
        except Exception as e:
            logger.error(f"Error creating demo users: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to initialize demo users: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Flogenix Enterprise Backend...")
    
    # Create database tables
    logger.info("Creating database tables...")
    init_database()
    
    # Create demo users for development
    if not is_production():
        logger.info("Creating demo users...")
        create_demo_users_if_needed()
    
    # Start Celery worker in background (development only)
    if not is_production():
        logger.info("Starting Celery worker for development...")
        # Note: In production, Celery workers should be started separately
    
    logger.info("✅ Flogenix Enterprise Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Flogenix Enterprise Backend...")
    
    # Close Celery connections
    celery_app.control.shutdown()
    
    logger.info("✅ Flogenix Enterprise Backend shutdown complete!")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    **Flogenix Enterprise Claims Processing Platform**
    
    Advanced AI-powered healthcare claims processing with:
    - 🤖 Multi-agent AI system with specialized processors
    - 🔐 Enterprise authentication with role-based access
    - ⚡ Real-time async processing with Celery
    - 🛡️ Comprehensive fraud detection
    - 📊 Advanced analytics and reporting
    - 🔍 Complete audit trails and compliance
    
    ## Authentication
    This API uses JWT Bearer token authentication. To access protected endpoints:
    1. Login via `/auth/login` to get access token
    2. Include token in Authorization header: `Bearer <token>`
    
    ## Multi-Agent Processing
    Claims are processed through a pipeline of specialized AI agents:
    - **Intake Agent**: Initial validation and data extraction
    - **Eligibility Agent**: Insurance coverage verification  
    - **Clinical Agent**: Medical necessity assessment
    - **Fraud Agent**: Risk analysis and fraud detection
    - **Adjudication Agent**: Final decision and reasoning
    """,
    version=settings.version,
    docs_url="/docs" if not is_production() else None,
    redoc_url="/redoc" if not is_production() else None,
    openapi_url="/openapi.json" if not is_production() else None,
    lifespan=lifespan
)

# Security middleware
if is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request size middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Limit request body size"""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > settings.api.max_request_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request too large. Maximum size: {settings.api.max_request_size} bytes"}
                )
    
    response = await call_next(request)
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if is_production():
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Include API routers
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    enterprise_claims_router,
    prefix="/api",
    tags=["Enterprise Claims"]
)

app.include_router(
    legacy_claims_router,
    prefix="/api",
    tags=["Legacy Claims"]
)

app.include_router(
    admin_router,
    prefix="/api/admin",
    tags=["Administration"]
)

# Notification endpoints
from app.api.simple_notifications import router as notifications_router
app.include_router(
    notifications_router,
    prefix="/api",
    tags=["Notifications"]
)

# Root and health endpoints
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "description": "Enterprise AI-powered healthcare claims processing platform",
        "features": [
            "Multi-agent AI processing",
            "Enterprise authentication",
            "Real-time async processing", 
            "Comprehensive fraud detection",
            "Advanced analytics",
            "Complete audit trails"
        ],
        "documentation": "/docs" if not is_production() else "Contact administrator",
        "status": "operational"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "environment": settings.environment,
        "database": "connected",  # TODO: Add actual DB health check
        "redis": "connected",     # TODO: Add actual Redis health check
        "celery": "connected"     # TODO: Add actual Celery health check
    }

@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Basic metrics endpoint"""
    # TODO: Implement comprehensive metrics
    return {
        "requests_total": 0,
        "active_users": 0,
        "claims_processing": 0,
        "uptime_seconds": 0
    }

# Custom OpenAPI documentation
def custom_openapi():
    """Custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if is_production():
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Configure OpenAPI documentation
app.openapi = lambda: custom_openapi(app)

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main_enterprise:app",
        host="0.0.0.0",
        port=8000,
        reload=not is_production(),
        log_level=settings.logging.level.lower(),
        access_log=True,
        workers=1 if not is_production() else 4
    )
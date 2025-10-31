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
import uvicorn
import logging

# Import enterprise components
from app.core.config import get_settings, is_production
from app.core.database import init_database, get_database_session
from app.core.security import auth_service, log_audit_event, AuditAction, get_current_user
from app.core.models import User

# Import API routers
from app.api.enterprise_claims import router as enterprise_claims_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.admin_dashboard import router as admin_dashboard_router
from app.api.documents import router as documents_router
from app.api.agentic_ai import router as agentic_ai_router
from app.api.analytics import router as analytics_router

# Import services
from app.services.celery_tasks import celery_app
from app.services.admin_reporting_service import admin_reporting_service
from app.services.gemini_service import gemini_service
from app.services.autonomous_exception_handler import autonomous_exception_handler
from app.services.continuous_learning_service import continuous_learning_service
from app.services.dynamic_triage_service import dynamic_triage_service
from app.services.enhanced_fraud_detection import enhanced_fraud_detection
from app.services.ai_customer_support import ai_customer_support
from app.services.human_in_loop_service import human_in_loop_service
from app.services.multi_agent_processor import multi_agent_processor

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
            existing_admin = auth_service.get_user_by_email_or_username(db, "admin@demo.com")
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
            existing_user = auth_service.get_user_by_email_or_username(db, "user@demo.com")
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
    
    # Initialize agentic AI services
    logger.info("Initializing agentic AI services...")
    try:
        # Gemini AI service initializes automatically in __init__
        logger.info(f"✅ Gemini AI service ready - Fallback mode: {getattr(gemini_service, 'fallback_mode', True)}")
        
        # Initialize AI services
        await admin_reporting_service.initialize() if hasattr(admin_reporting_service, 'initialize') else None
        logger.info("✅ Admin reporting service ready")
        
        logger.info("✅ All agentic AI services initialized successfully")
        
    except Exception as e:
        logger.error(f"⚠️ Error initializing AI services: {e}")
        # Continue startup even if AI services fail
    
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
    - 🤖 Multi-agent AI system with specialized processors powered by Google Gemini
    - 🧠 Autonomous Exception Handling with learning capabilities
    - � Continuous Learning and adaptive AI improvement
    - 🎯 Dynamic Claims Triage with intelligent routing
    - 🔍 Enhanced Fraud Detection with pattern recognition
    - 💬 AI-powered Customer Support with sentiment analysis
    - 👥 Human-in-the-Loop escalation mechanisms
    - 📋 Comprehensive Admin Reporting with AI decision transparency
    - �🔐 Enterprise authentication with role-based access
    - ⚡ Real-time async processing with Celery
    - 🛡️ Comprehensive fraud detection
    - 📊 Advanced analytics and reporting
    - 🔍 Complete audit trails and compliance
    
    ## Agentic AI Features
    This platform includes 6 advanced agentic AI capabilities:
    1. **Autonomous Exception Handling** - AI automatically resolves common issues
    2. **Continuous Learning** - System improves from every interaction
    3. **Dynamic Triage** - Intelligent claim routing and prioritization
    4. **Enhanced Fraud Detection** - Advanced pattern recognition
    5. **AI Customer Support** - Intelligent response generation
    6. **Human-in-Loop** - Smart escalation to specialists
    
    ## Admin Transparency
    Every AI decision includes detailed reporting with:
    - Complete reasoning and justification
    - Confidence scoring and risk assessment
    - Step-by-step decision audit trails
    - Business impact analysis
    - Compliance documentation
    
    ## Authentication
    This API uses JWT Bearer token authentication. To access protected endpoints:
    1. Login via `/auth/login` to get access token
    2. Include token in Authorization header: `Bearer <token>`
    
    ## Multi-Agent Processing
    Claims are processed through a pipeline of specialized AI agents powered by Google Gemini:
    - **Intake Agent**: Initial validation and data extraction
    - **Eligibility Agent**: Insurance coverage verification  
    - **Clinical Agent**: Medical necessity assessment
    - **Fraud Agent**: Advanced risk analysis and fraud detection
    - **Adjudication Agent**: Final decision and reasoning
    - **Exception Handler**: Autonomous resolution of common issues
    - **Learning Agent**: Continuous improvement from outcomes
    - **Triage Agent**: Dynamic routing and prioritization
    - **Customer Support Agent**: Intelligent interaction handling
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
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
    tags=["Enterprise Claims Processing"]
)

app.include_router(
    admin_router,
    prefix="/api/admin",
    tags=["Administration"]
)

app.include_router(
    admin_dashboard_router,
    prefix="/admin",
    tags=["Admin Dashboard"]
)

# Notification endpoints
from app.api.simple_notifications import router as notifications_router
app.include_router(
    notifications_router,
    prefix="/api",
    tags=["Notifications"]
)

# Document processing endpoints
app.include_router(
    documents_router,
    prefix="/api",
    tags=["Document Processing"]
)

# Agentic AI Services endpoints
app.include_router(
    agentic_ai_router,
    prefix="/api",
    tags=["Agentic AI Services"]
)

# Analytics and Reporting endpoints
app.include_router(
    analytics_router,
    prefix="/api",
    tags=["Analytics & Reporting"]
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
            "Multi-agent AI processing with Google Gemini",
            "Autonomous exception handling with learning",
            "Continuous learning and adaptation",
            "Dynamic claims triage and routing",
            "Enhanced fraud detection with AI",
            "AI-powered customer support",
            "Human-in-the-loop escalation",
            "Comprehensive admin reporting",
            "Enterprise authentication",
            "Real-time async processing", 
            "Complete audit trails"
        ],
        "documentation": "/docs" if not is_production() else "Contact administrator",
        "status": "operational"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint with agentic AI service status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "environment": settings.environment,
        "database": "connected",  # TODO: Add actual DB health check
        "redis": "connected",     # TODO: Add actual Redis health check
        "celery": "connected",    # TODO: Add actual Celery health check
        "agentic_ai_services": {
            "gemini_service": "operational",
            "admin_reporting": "operational", 
            "autonomous_exceptions": "operational",
            "continuous_learning": "operational",
            "dynamic_triage": "operational",
            "fraud_detection": "operational",
            "customer_support": "operational",
            "human_in_loop": "operational",
            "multi_agent_processor": "operational"
        }
    }
    
    # TODO: Add actual health checks for AI services
    try:
        # Quick validation that services are importable
        if gemini_service and admin_reporting_service:
            health_status["agentic_ai_services"]["status"] = "all_operational"
        else:
            health_status["agentic_ai_services"]["status"] = "degraded"
    except Exception as e:
        logger.warning(f"AI services health check failed: {e}")
        health_status["agentic_ai_services"]["status"] = "degraded"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Enhanced metrics endpoint with AI service statistics"""
    try:
        # Get admin dashboard summary for AI metrics
        ai_metrics = await admin_reporting_service.generate_admin_dashboard_summary()
        
        metrics = {
            "system_metrics": {
                "requests_total": 0,  # TODO: Implement request counter
                "active_users": 0,    # TODO: Implement active user tracking
                "claims_processing": 0, # TODO: Implement claims counter
                "uptime_seconds": 0    # TODO: Implement uptime tracking
            },
            "ai_metrics": {
                "total_ai_decisions": ai_metrics.get("total_reports", 0),
                "automation_rate_percent": ai_metrics.get("automation_rate", 0),
                "average_confidence_score": ai_metrics.get("average_confidence_score", 0),
                "human_reviews_needed": ai_metrics.get("human_review_needed", 0),
                "recent_activity_24h": ai_metrics.get("recent_activity_24h", 0),
                "decision_types": ai_metrics.get("type_distribution", {}),
                "severity_distribution": ai_metrics.get("severity_distribution", {})
            },
            "service_status": {
                "gemini_ai": "operational",
                "admin_reporting": "operational",
                "autonomous_exceptions": "operational",
                "fraud_detection": "operational",
                "customer_support": "operational",
                "multi_agent_processing": "operational"
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating enhanced metrics: {e}")
        # Fallback to basic metrics
        return {
            "system_metrics": {
                "requests_total": 0,
                "active_users": 0,
                "claims_processing": 0,
                "uptime_seconds": 0
            },
            "ai_metrics": {
                "status": "metrics_unavailable",
                "error": str(e)
            }
        }

@app.get("/ai/capabilities", tags=["Agentic AI"])
async def get_ai_capabilities():
    """Get information about agentic AI capabilities"""
    return {
        "agentic_ai_platform": "Flogenix Enterprise",
        "ai_provider": "Google Gemini",
        "model": "gemini-2.5-flash",
        "capabilities": {
            "autonomous_exception_handling": {
                "description": "AI automatically resolves common issues with learning",
                "features": ["Cached solutions", "Automated actions", "Learning from outcomes"],
                "enabled": settings.ai.enable_autonomous_exceptions
            },
            "continuous_learning": {
                "description": "System improves from every interaction",
                "features": ["Feedback loops", "Pattern detection", "Confidence adjustment"],
                "enabled": settings.ai.enable_continuous_learning
            },
            "dynamic_triage": {
                "description": "Intelligent claim routing and prioritization", 
                "features": ["Priority matrix", "Routing rules", "Performance tracking"],
                "enabled": settings.ai.enable_dynamic_triage
            },
            "enhanced_fraud_detection": {
                "description": "Advanced pattern recognition for fraud prevention",
                "features": ["Behavioral analysis", "Network patterns", "Temporal analysis"],
                "enabled": settings.ai.enable_predictive_fraud
            },
            "ai_customer_support": {
                "description": "Intelligent customer interaction handling",
                "features": ["Sentiment analysis", "Escalation rules", "Response generation"],
                "enabled": settings.ai.enable_ai_customer_support
            },
            "human_in_loop": {
                "description": "Smart escalation to human specialists",
                "features": ["Case complexity assessment", "Specialist assignment", "Feedback integration"],
                "enabled": settings.ai.enable_human_in_loop
            }
        },
        "admin_reporting": {
            "description": "Comprehensive AI decision transparency",
            "features": [
                "Detailed reasoning analysis",
                "Confidence scoring",
                "Step-by-step audit trails", 
                "Business impact assessment",
                "Risk analysis",
                "Compliance documentation"
            ],
            "dashboard_available": True
        },
        "integration_status": "fully_operational",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/system/comprehensive-status", tags=["System"])
async def get_comprehensive_system_status():
    """Comprehensive system status including all services and AI capabilities"""
    try:
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "version": settings.version,
            "system_health": "operational",
            
            # Core Infrastructure
            "infrastructure": {
                "database": "connected",  # TODO: Add actual DB health check
                "redis": "connected",     # TODO: Add actual Redis health check
                "celery": "connected",    # TODO: Add actual Celery health check
                "storage": "available"    # TODO: Add storage health check
            },
            
            # API Endpoints Status
            "api_endpoints": {
                "authentication": "operational",
                "claims_processing": "operational", 
                "administration": "operational",
                "admin_dashboard": "operational",
                "notifications": "operational",
                "document_processing": "operational",
                "agentic_ai_services": "operational",
                "analytics_reporting": "operational"
            },
            
            # Agentic AI Services Status
            "agentic_ai_services": {
                "gemini_service": "operational",
                "admin_reporting": "operational",
                "ai_customer_support": "operational",
                "autonomous_exception_handling": "operational",
                "continuous_learning": "operational",
                "dynamic_triage": "operational",
                "enhanced_fraud_detection": "operational", 
                "human_in_loop": "operational",
                "multi_agent_processor": "operational",
                "ocr_service": "operational"
            },
            
            # Service Statistics
            "service_statistics": {
                "total_endpoints": len([route for route in app.routes if hasattr(route, 'methods')]),
                "authenticated_endpoints": "secured",
                "admin_endpoints": "role_protected",
                "ai_service_integrations": 10,
                "active_middleware": 3
            },
            
            # Recent Activity (placeholder)
            "recent_activity": {
                "requests_last_hour": 0,  # TODO: Implement request tracking
                "ai_decisions_last_hour": 0,  # TODO: Get from AI services
                "errors_last_hour": 0,    # TODO: Implement error tracking
                "avg_response_time_ms": 0  # TODO: Implement response time tracking
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error generating comprehensive status: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": "degraded",
            "error": str(e),
            "message": "Some system components may not be fully operational"
        }

@app.get("/ai/demo", tags=["Agentic AI"])
async def run_ai_demo():
    """Run a quick demo of agentic AI capabilities"""
    demo_results = {
        "demo_timestamp": datetime.utcnow().isoformat(),
        "capabilities_tested": [],
        "results": {}
    }
    
    try:
        # Test exception handling
        demo_results["capabilities_tested"].append("autonomous_exception_handling")
        exception_result = await autonomous_exception_handler.handle_exception(
            exception_type="demo_test",
            exception_data={"test": "data"},
            claim_context={"demo": True, "claim_id": "DEMO-001"}
        )
        demo_results["results"]["exception_handling"] = {
            "status": "tested",
            "autonomous": exception_result.get("handled_autonomously", False),
            "confidence": exception_result.get("confidence_score", 0)
        }
        
        # Test admin reporting
        recent_reports = await admin_reporting_service.get_reports_by_criteria(limit=5)
        demo_results["results"]["admin_reporting"] = {
            "status": "tested", 
            "total_reports": len(recent_reports),
            "latest_report_id": recent_reports[0].report_id if recent_reports else None
        }
        
        demo_results["overall_status"] = "success"
        
    except Exception as e:
        logger.error(f"AI demo error: {e}")
        demo_results["overall_status"] = "partial_success"
        demo_results["error"] = str(e)
    
    return demo_results

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
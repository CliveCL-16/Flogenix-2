# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.enterprise_claims import router as claims_router

# Create FastAPI app
app = FastAPI(
    title="Flowgenix API",
    description="Intelligent Autonomous Healthcare Claims Approval Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",  # Vite dev server
        "http://localhost:8080", "http://127.0.0.1:8080",  # Alternative ports
        "http://localhost:3000", "http://127.0.0.1:3000",  # React default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(claims_router, prefix="/api", tags=["claims"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Flowgenix API",
        "description": "Intelligent Autonomous Healthcare Claims Approval Platform",
        "docs": "/docs",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify server is working"""
    return {"status": "ok", "message": "Server is working correctly"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

import os
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback

from config import settings
from routers import projects, csd, pvb, bmc, rice, roadmap, okr, ai, reports
from auth import router as auth_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize any resources on startup
    # (None needed with Supabase for database connections)
    logger.info("Starting application...")
    logger.info(f"CORS origins: {settings.cors_origins}")
    yield
    # Clean up any resources on shutdown
    logger.info("Shutting down application...")

app = FastAPI(
    title="Product Discovery Hub API",
    description="Backend API for Product Discovery Hub",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http(s)?:\/\/(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Add error logging middleware
@app.middleware("http")
async def log_errors(request: Request, call_next):
    try:
        # Log request information
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Request headers: {request.headers}")
        
        response = await call_next(request)
        
        # Log response information
        logger.info(f"Response status code: {response.status_code}")
        
        return response
    except Exception as e:
        logger.error(f"Request to {request.url} failed: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Simple CORS test endpoint
@app.options("/api/cors-test")
@app.get("/api/cors-test")
async def cors_test():
    """Simple endpoint to test CORS configuration"""
    logger.info("CORS test endpoint called")
    return {"message": "CORS is working!"}

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(csd.router, prefix="/api", tags=["csd"])
app.include_router(pvb.router, prefix="/api", tags=["pvb"])
app.include_router(bmc.router, prefix="/api", tags=["bmc"])
app.include_router(rice.router, prefix="/api", tags=["rice"])
app.include_router(roadmap.router, prefix="/api", tags=["roadmap"])
app.include_router(okr.router, prefix="/api", tags=["okr"])
app.include_router(ai.router, prefix="/api", tags=["ai"])
app.include_router(reports.router, prefix="/api", tags=["reports"])

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": app.version}

@app.get("/")
async def root():
    """Root endpoint that redirects to docs"""
    return {
        "message": "Welcome to Product Discovery Hub API",
        "documentation": "/docs"
    } 
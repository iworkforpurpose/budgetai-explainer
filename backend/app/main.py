"""
Budget 2026 AI - FastAPI Application
Production-ready backend with RAG using Groq LLM
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.v1.router import router as api_v1_router
from .core.config import settings
from .core.logger import setup_logger

logger = setup_logger(__name__)


# Startup/shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Budget 2026 AI Backend...")
    logger.info("⚠ Running with lazy loading to fit in 512MB RAM")
    logger.info("Models will load on first request (~10-15s delay)")
    
    # Skip pre-loading to save memory on Render free tier
    # Models will load on first API call instead
    
    yield
    
    # Shutdown
    logger.info("Shutting down Budget 2026 AI Backend...")


# Create FastAPI app
app = FastAPI(
    title="Budget 2026 AI API",
    description="AI-powered Budget 2026 explainer with RAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Budget 2026 AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

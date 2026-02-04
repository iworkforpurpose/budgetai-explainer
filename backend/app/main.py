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
    
    # Pre-load models
    try:
        from .rag.embeddings_local import LocalEmbeddingGenerator
        from .rag.vector_store import SupabaseVectorStore
        from .llm.groq_client import get_groq_client
        
        logger.info("Loading embedding model...")
        embedder = LocalEmbeddingGenerator()
        
        logger.info("Connecting to Supabase...")
        store = SupabaseVectorStore()
        count = store.get_chunk_count()
        logger.info(f"Connected to Supabase: {count} chunks available")
        
        logger.info("Initializing Groq client...")
        llm = get_groq_client()
        
        logger.info("✓ All components initialized successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
    
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

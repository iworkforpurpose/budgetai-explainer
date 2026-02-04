"""
Health check endpoint
"""
from fastapi import APIRouter

from ..models import HealthResponse
from ....rag.vector_store import SupabaseVectorStore
from ....llm.groq_client import get_groq_client
from ....core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns status of all system components
    """
    components = {}
    
    # Check database
    try:
        store = SupabaseVectorStore()
        count = store.get_chunk_count()
        components["database"] = f"ok ({count} chunks)"
    except Exception as e:
        components["database"] = f"error: {str(e)[:50]}"
    
    # Check embedding model
    try:
        from ....rag.embeddings_local import LocalEmbeddingGenerator
        embedder = LocalEmbeddingGenerator()
        components["embedding_model"] = "loaded"
    except Exception as e:
        components["embedding_model"] = f"error: {str(e)[:50]}"
    
    # Check Groq API
    try:
        llm = get_groq_client()
        components["groq_api"] = "ok"
    except Exception as e:
        components["groq_api"] = f"error: {str(e)[:50]}"
    
    # Overall status
    all_ok = all("ok" in status or "loaded" in status for status in components.values())
    
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        components=components,
        version="1.0.0"
    )

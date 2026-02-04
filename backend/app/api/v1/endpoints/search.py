"""
Search endpoint - Direct vector search
"""
from fastapi import APIRouter, HTTPException, Query

from ..models import SearchResponse, SearchResult
from ....rag.embeddings_local import LocalEmbeddingGenerator
from ....rag.vector_store import SupabaseVectorStore
from ....core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Initialize components
embedder = LocalEmbeddingGenerator()
vector_store = SupabaseVectorStore()


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Similarity threshold")
):
    """
    Direct vector search without LLM generation
    
    Returns relevant budget document chunks
    """
    try:
        logger.info(f"Search request: {q[:100]}")
        
        # Generate embedding
        query_embedding = embedder.generate_embedding(q)
        
        # Search
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=limit,
            threshold=threshold
        )
        
        # Format response
        return SearchResponse(
            results=[
                SearchResult(
                    text=r['text'],
                    document=r['document_name'],
                    page=r['page_number'],
                    similarity=r['similarity'],
                    metadata=r.get('metadata')
                )
                for r in results
            ],
            total=len(results)
        )
    
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process search request")

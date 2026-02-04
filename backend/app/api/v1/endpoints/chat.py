"""
Chat endpoint - Main RAG interface
"""
from fastapi import APIRouter, HTTPException
from uuid import uuid4

from ..models import ChatRequest, ChatResponse, Source
from ....rag.rag_pipeline import get_rag_pipeline
from ....core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG
    
    Process user question with retrieval-augmented generation
    """
    try:
        logger.info(f"Chat request: {request.message[:100]}")
        
        # Get RAG pipeline
        rag = get_rag_pipeline()
        
        # Process query
        result = rag.query(
            question=request.message,
            user_metadata=request.user_metadata
        )
        
        # Format response
        return ChatResponse(
            answer=result['answer'],
            sources=[Source(**source) for source in result['sources']],
            conversation_id=request.conversation_id or str(uuid4())
        )
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process chat request")

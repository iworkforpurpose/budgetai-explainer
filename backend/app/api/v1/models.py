"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=1000, description="User's question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    user_metadata: Optional[Dict] = Field(None, description="User metadata for filtering")


class Source(BaseModel):
    """Source citation model"""
    document: str
    page: int
    similarity: float
    excerpt: str


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    sources: List[Source]
    conversation_id: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(5, ge=1, le=20)
    threshold: float = Field(0.3, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """Search result model"""
    text: str
    document: str
    page: int
    similarity: float
    metadata: Optional[Dict] = None


class SearchResponse(BaseModel):
    """Search response model"""
    results: List[SearchResult]
    total: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    components: Dict[str, str]
    version: str

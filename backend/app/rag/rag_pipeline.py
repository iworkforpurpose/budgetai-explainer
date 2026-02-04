"""
Complete RAG Pipeline
Retrieves relevant chunks and generates responses using Groq LLM
"""
from typing import Dict, List, Optional

from .embeddings_local import LocalEmbeddingGenerator
from .vector_store import SupabaseVectorStore
from ..llm.groq_client import get_groq_client
from ..llm.prompts import (
    SYSTEM_PROMPT,
    create_rag_prompt,
    create_no_context_prompt,
    format_response_with_sources
)
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline: Retrieve + Generate
    """
    
    def __init__(
        self,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        max_context_chunks: int = 3
    ):
        """
        Initialize RAG pipeline
        
        Args:
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity score
            max_context_chunks: Max chunks to use in context
        """
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.max_context_chunks = max_context_chunks
        
        # Initialize components
        self.embedder = LocalEmbeddingGenerator()
        self.vector_store = SupabaseVectorStore()
        self.llm = get_groq_client()
        
        logger.info(
            "Initialized RAGPipeline",
            extra=log_extra(
                top_k=top_k,
                threshold=similarity_threshold,
                max_context=max_context_chunks
            )
        )
    
    def retrieve(
        self,
        query: str,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for query
        
        Args:
            query: User's question
            filters: Optional metadata filters
            
        Returns:
            List of relevant chunks with similarity scores
        """
        logger.info(f"Retrieving context for query: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            k=self.top_k,
            threshold=self.similarity_threshold,
            filters=filters or {}
        )
        
        logger.info(
            f"Retrieved {len(results)} chunks",
            extra=log_extra(
                num_results=len(results),
                avg_similarity=sum(r['similarity'] for r in results) / len(results) if results else 0
            )
        )
        
        return results
    
    def generate(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> Dict:
        """
        Generate response using LLM with retrieved context
        
        Args:
            query: User's question
            context_chunks: Retrieved chunks
            
        Returns:
            Response dict with answer and sources
        """
        # Select top chunks for context (by similarity)
        top_chunks = sorted(
            context_chunks,
            key=lambda x: x['similarity'],
            reverse=True
        )[:self.max_context_chunks]
        
        # Create prompt
        if top_chunks:
            user_prompt = create_rag_prompt(query, top_chunks)
        else:
            user_prompt = create_no_context_prompt(query)
            logger.warning("No context found for query")
        
        # Generate response
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        response_text = self.llm.chat_completion(messages)
        
        # Format response with sources
        return format_response_with_sources(response_text, top_chunks)
    
    def query(
        self,
        question: str,
        user_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Complete RAG query: retrieve + generate
        
        Args:
            question: User's question
            user_metadata: Optional user metadata for filtering
            
        Returns:
            Response dict with answer and sources
        """
        logger.info(
            f"Processing RAG query",
            extra=log_extra(query=question[:100])
        )
        
        # Step 1: Retrieve
        chunks = self.retrieve(question, filters=user_metadata)
        
        # Step 2: Generate
        response = self.generate(question, chunks)
        
        logger.info(
            "RAG query completed",
            extra=log_extra(
                num_sources=len(response['sources']),
                answer_length=len(response['answer'])
            )
        )
        
        return response


# Singleton instance
_rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    """Get singleton RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

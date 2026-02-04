"""
Supabase vector store integration for Budget 2026 AI Platform
Uses pgvector for semantic similarity search
"""
from typing import List, Dict, Optional, Tuple
import json
from supabase import create_client, Client

from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


class SupabaseVectorStore:
    """
    Vector store using Supabase with pgvector extension
    Optimized for Render free tier deployment
    """
    
    def __init__(
        self,
        supabase_url: str = None,
        supabase_key: str = None,
        table_name: str = "budget_chunks"
    ):
        """
        Initialize Supabase vector store
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/service key
            table_name: Name of the table storing vectors
        """
        self.supabase_url = supabase_url or settings.SUPABASE_URL
        self.supabase_key = supabase_key or settings.SUPABASE_KEY
        self.table_name = table_name
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        # Initialize client (no proxy parameter in v2.3.4)
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        logger.info(
            f"Initialized SupabaseVectorStore",
            extra=log_extra(table=table_name)
        )
    
    def create_table(self):
        """
        Create the budget_chunks table with pgvector extension
        
        Run this SQL in Supabase SQL Editor:
        
        -- Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Create table
        CREATE TABLE IF NOT EXISTS budget_chunks (
          id BIGSERIAL PRIMARY KEY,
          chunk_id TEXT UNIQUE NOT NULL,
          document_name TEXT NOT NULL,
          page_number INTEGER,
          chunk_index INTEGER,
          text TEXT NOT NULL,
          word_count INTEGER,
          quality_score FLOAT,
          
          -- Embedding
          embedding vector(1536),
          embedding_model TEXT,
          
          -- Metadata (JSONB for flexible querying)
          metadata JSONB,
          
          -- Versioning
          pipeline_version TEXT,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_document_name ON budget_chunks(document_name);
        CREATE INDEX IF NOT EXISTS idx_quality_score ON budget_chunks(quality_score);
        CREATE INDEX IF NOT EXISTS idx_metadata_gin ON budget_chunks USING GIN(metadata);
        
        -- Vector similarity index (IVFFlat for fast approximate search)
        CREATE INDEX IF NOT EXISTS idx_embedding_vector 
        ON budget_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        
        -- Function for similarity search
        CREATE OR REPLACE FUNCTION match_budget_chunks(
          query_embedding vector(1536),
          match_threshold float DEFAULT 0.5,
          match_count int DEFAULT 5,
          filter_metadata jsonb DEFAULT '{}'::jsonb
        )
        RETURNS TABLE (
          chunk_id text,
          document_name text,
          page_number int,
          text text,
          metadata jsonb,
          similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
          RETURN QUERY
          SELECT
            budget_chunks.chunk_id,
            budget_chunks.document_name,
            budget_chunks.page_number,
            budget_chunks.text,
            budget_chunks.metadata,
            1 - (budget_chunks.embedding <=> query_embedding) as similarity
          FROM budget_chunks
          WHERE 
            (filter_metadata = '{}'::jsonb OR budget_chunks.metadata @> filter_metadata)
            AND 1 - (budget_chunks.embedding <=> query_embedding) > match_threshold
          ORDER BY budget_chunks.embedding <=> query_embedding
          LIMIT match_count;
        END;
        $$;
        """
        print(self.create_table.__doc__)
        logger.info("Table creation SQL printed. Run it in Supabase SQL Editor.")
    
    def upload_chunk(self, chunk: Dict) -> bool:
        """
        Upload a single chunk to Supabase
        
        Args:
            chunk: Chunk dictionary with embedding
            
        Returns:
            Success boolean
        """
        try:
            # Prepare data
            data = {
                'chunk_id': chunk['chunk_id'],
                'document_name': chunk['document_name'],
                'page_number': chunk['page_number'],
                'chunk_index': chunk['chunk_index'],
                'text': chunk['text'],
                'word_count': chunk['word_count'],
                'quality_score': chunk.get('quality_score', 1.0),
                'embedding': chunk['embedding'],
                'embedding_model': chunk.get('embedding_model', 'unknown'),
                'metadata': chunk.get('metadata', {}),
                'pipeline_version': chunk.get('metadata', {}).get('pipeline_version', 'v1.0')
            }
            
            # Insert (upsert to handle duplicates)
            self.client.table(self.table_name).upsert(data).execute()
            
            return True
        
        except Exception as e:
            logger.error(
                f"Failed to upload chunk {chunk.get('chunk_id', 'unknown')}: {str(e)}",
                exc_info=True
            )
            return False
    
    def upload_chunks_batch(
        self,
        chunks: List[Dict],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Upload multiple chunks in batches
        
        Args:
            chunks: List of chunk dictionaries with embeddings
            batch_size: Number of chunks per batch
            
        Returns:
            Statistics dictionary
        """
        logger.info(
            f"Uploading {len(chunks)} chunks to Supabase",
            extra=log_extra(batch_size=batch_size)
        )
        
        success_count = 0
        failed_count = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            logger.info(
                f"Uploading batch {batch_num}/{total_batches}",
                extra=log_extra(size=len(batch))
            )
            
            try:
                # Prepare batch data
                batch_data = []
                for chunk in batch:
                    batch_data.append({
                        'chunk_id': chunk['chunk_id'],
                        'document_name': chunk['document_name'],
                        'page_number': chunk['page_number'],
                        'chunk_index': chunk['chunk_index'],
                        'text': chunk['text'],
                        'word_count': chunk['word_count'],
                        'quality_score': chunk.get('quality_score', 1.0),
                        'embedding': chunk['embedding'],
                        'embedding_model': chunk.get('embedding_model', 'unknown'),
                        'metadata': chunk.get('metadata', {}),
                        'pipeline_version': chunk.get('metadata', {}).get('pipeline_version', 'v1.0')
                    })
                
                # Batch upsert
                self.client.table(self.table_name).upsert(batch_data).execute()
                success_count += len(batch)
            
            except Exception as e:
                logger.error(
                    f"Batch {batch_num} upload failed: {str(e)}",
                    extra=log_extra(batch_start=i, batch_end=i+len(batch)),
                    exc_info=True
                )
                failed_count += len(batch)
        
        stats = {
            'total': len(chunks),
            'success': success_count,
            'failed': failed_count
        }
        
        logger.info(
            "Upload completed",
            extra=log_extra(**stats)
        )
        
        return stats
    
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        threshold: float = 0.5,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Search for similar chunks using vector similarity
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            threshold: Minimum similarity threshold (0-1)
            filters: Metadata filters (JSONB contains query)
            
        Returns:
            List of matching chunks with similarity scores
        """
        try:
            # Call the match function
            filter_metadata = filters or {}
            
            result = self.client.rpc(
                'match_budget_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': k,
                    'filter_metadata': filter_metadata
                }
            ).execute()
            
            return result.data
        
        except Exception as e:
            logger.error(
                f"Similarity search failed: {str(e)}",
                extra=log_extra(k=k, threshold=threshold),
                exc_info=True
            )
            return []
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks in database"""
        try:
            result = self.client.table(self.table_name).select('id', count='exact').execute()
            return result.count
        except Exception as e:
            logger.error(f"Failed to get chunk count: {str(e)}")
            return 0
    
    def delete_all_chunks(self):
        """Delete all chunks (use with caution!)"""
        logger.warning("Deleting all chunks from database")
        try:
            self.client.table(self.table_name).delete().neq('id', 0).execute()
            logger.info("All chunks deleted")
        except Exception as e:
            logger.error(f"Failed to delete chunks: {str(e)}")


if __name__ == "__main__":
    # Print table creation SQL
    print("=" * 70)
    print("Supabase Vector Store - Table Creation")
    print("=" * 70)
    
    store = SupabaseVectorStore()
    store.create_table()
    
    print("\n" + "=" * 70)
    print("Copy the SQL above and run it in Supabase SQL Editor")
    print("=" * 70)

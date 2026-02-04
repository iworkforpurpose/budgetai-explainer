"""
Embedding generation for Budget 2026 AI Platform
Uses OpenAI API (lightweight, no local models needed)
"""
from typing import List, Dict, Optional
import time
from openai import OpenAI

from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI API
    Optimized for Render deployment (no local models)
    """
    
    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize embedding generator
        
        Args:
            model: OpenAI embedding model
                   - text-embedding-3-small (1536 dim, $0.02/1M tokens)
                   - text-embedding-3-large (3072 dim, $0.13/1M tokens)
        """
        self.model = model
        self.dimension = 1536 if "small" in model else 3072
        
        # Initialize OpenAI client
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info(
            f"Initialized EmbeddingGenerator",
            extra=log_extra(model=model, dimension=self.dimension)
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimension
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text[:8000]  # OpenAI limit is 8191 tokens
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(
                f"Failed to generate embedding: {str(e)}",
                extra=log_extra(text_length=len(text)),
                exc_info=True
            )
            # Return zero vector on error
            return [0.0] * self.dimension
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        delay: float = 0.1
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (max 2048 for OpenAI)
            delay: Delay between batches (rate limiting)
            
        Returns:
            List of embedding vectors
        """
        logger.info(
            f"Generating embeddings for {len(texts)} texts",
            extra=log_extra(batch_size=batch_size, total=len(texts))
        )
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            logger.info(
                f"Processing batch {batch_num}/{total_batches}",
                extra=log_extra(batch_size=len(batch))
            )
            
            try:
                # Clean texts (remove empty ones)
                clean_batch = [t[:8000] if t else " " for t in batch]
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=clean_batch
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                # Rate limiting
                if delay > 0 and i + batch_size < len(texts):
                    time.sleep(delay)
            
            except Exception as e:
                logger.error(
                    f"Batch {batch_num} failed: {str(e)}",
                    extra=log_extra(batch_start=i, batch_end=i+len(batch)),
                    exc_info=True
                )
                # Add zero vectors for failed batch
                embeddings.extend([[0.0] * self.dimension] * len(batch))
        
        logger.info(
            f"Generated {len(embeddings)} embeddings",
            extra=log_extra(
                success_rate=sum(1 for e in embeddings if sum(e) != 0) / len(embeddings) * 100
            )
        )
        
        return embeddings
    
    def embed_chunks(
        self,
        chunks: List[Dict],
        text_field: str = 'text',
        batch_size: int = 100
    ) -> List[Dict]:
        """
        Add embeddings to chunk dictionaries
        
        Args:
            chunks: List of chunk dictionaries
            text_field: Field name containing text to embed
            batch_size: Batch size for API calls
            
        Returns:
            Chunks with 'embedding' field added
        """
        logger.info(
            f"Embedding {len(chunks)} chunks",
            extra=log_extra(text_field=text_field)
        )
        
        # Extract texts
        texts = [chunk.get(text_field, '') for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts, batch_size=batch_size)
        
        # Add to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
            chunk['embedding_model'] = self.model
            chunk['embedding_dimension'] = self.dimension
        
        logger.info(
            f"Embeddings added to {len(chunks)} chunks",
            extra=log_extra(dimension=self.dimension)
        )
        
        return chunks


# Convenience function
def generate_embeddings_for_file(
    input_file: str,
    output_file: str = None,
    batch_size: int = 100
) -> List[Dict]:
    """
    Load chunks from file, generate embeddings, and save
    
    Args:
        input_file: Path to chunks JSON file
        output_file: Path to save embedded chunks (optional)
        batch_size: Batch size for API calls
        
    Returns:
        Chunks with embeddings
    """
    import json
    from pathlib import Path
    
    logger.info(f"Loading chunks from {input_file}")
    
    # Load chunks
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'chunks' in data:
        chunks = data['chunks']
    elif isinstance(data, list):
        chunks = data
    else:
        raise ValueError("Unexpected file format")
    
    # Generate embeddings
    generator = EmbeddingGenerator()
    embedded_chunks = generator.embed_chunks(chunks, batch_size=batch_size)
    
    # Save if output specified
    if output_file:
        logger.info(f"Saving embedded chunks to {output_file}")
        
        output_data = {
            'metadata': data.get('metadata', {}) if isinstance(data, dict) else {},
            'chunks': embedded_chunks
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
    
    return embedded_chunks


if __name__ == "__main__":
    # Test embedding generator
    print("🔮 Testing Embedding Generator\n")
    
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set in environment")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    # Test single embedding
    generator = EmbeddingGenerator()
    
    test_text = "The Finance Bill proposes tax relief for salaried individuals."
    print(f"Test text: {test_text}")
    
    embedding = generator.generate_embedding(test_text)
    print(f"\n✓ Embedding generated")
    print(f"  Dimension: {len(embedding)}")
    print(f"  Sample values: {embedding[:5]}")
    print(f"  Model: {generator.model}")

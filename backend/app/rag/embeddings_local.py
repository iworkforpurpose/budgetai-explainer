"""
Local embedding generation using sentence-transformers
100% free, no API needed
"""
from typing import List, Dict
import time
from sentence_transformers import SentenceTransformer

from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


class LocalEmbeddingGenerator:
    """
    Generate embeddings using local sentence-transformers model
    Free, runs on CPU, no API costs
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize local embedding generator
        
        Args:
            model_name: HuggingFace model name
                       - all-MiniLM-L6-v2 (384 dim, fastest, recommended)
                       - all-mpnet-base-v2 (768 dim, more accurate, slower)
        """
        self.model_name = model_name
        self.dimension = 384 if "MiniLM" in model_name else 768
        
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        logger.info(
            "Initialized LocalEmbeddingGenerator",
            extra=log_extra(model=model_name, dimension=self.dimension)
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
            embedding = self.model.encode(text, show_progress_bar=False)
            return embedding.tolist()
        
        except Exception as e:
            logger.error(
                f"Failed to generate embedding: {str(e)}",
                extra=log_extra(text_length=len(text)),
                exc_info=True
            )
            return [0.0] * self.dimension
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
        """
        logger.info(
            f"Generating embeddings for {len(texts)} texts",
            extra=log_extra(batch_size=batch_size, total=len(texts))
        )
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            return embeddings.tolist()
        
        except Exception as e:
            logger.error(
                f"Batch embedding failed: {str(e)}",
                exc_info=True
            )
            return [[0.0] * self.dimension] * len(texts)
    
    def embed_chunks(
        self,
        chunks: List[Dict],
        text_field: str = 'text',
        batch_size: int = 32
    ) -> List[Dict]:
        """
        Add embeddings to chunk dictionaries
        
        Args:
            chunks: List of chunk dictionaries
            text_field: Field name containing text to embed
            batch_size: Batch size for encoding
            
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
            chunk['embedding_model'] = self.model_name
            chunk['embedding_dimension'] = self.dimension
        
        logger.info(
            f"Embeddings added to {len(chunks)} chunks",
            extra=log_extra(dimension=self.dimension)
        )
        
        return chunks


if __name__ == "__main__":
    # Test embedding generator
    print("🔮 Testing Local Embedding Generator\n")
    
    # Test single embedding
    generator = LocalEmbeddingGenerator()
    
    test_text = "The Finance Bill proposes tax relief for salaried individuals."
    print(f"Test text: {test_text}")
    
    embedding = generator.generate_embedding(test_text)
    print(f"\n✓ Embedding generated")
    print(f"  Dimension: {len(embedding)}")
    print(f"  Sample values: {embedding[:5]}")
    print(f"  Model: {generator.model_name}")

"""
Text splitter for Budget 2026 AI Platform
Chunks documents into semantic pieces while preserving context
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import re

from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    chunk_id: str
    document_name: str
    page_number: int
    chunk_index: int
    text: str
    char_count: int
    word_count: int
    token_count: int  # Approximate
    quality_score: float = 1.0  # 0-1 score for chunk quality
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class SemanticTextSplitter:
    """
    Smart text splitter that:
    - Respects sentence boundaries
    - Maintains context with overlap
    - Preserves semantic coherence
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = 100
    ):
        """
        Initialize text splitter
        
        Args:
            chunk_size: Target chunk size in tokens (default from settings)
            chunk_overlap: Overlap between chunks in tokens (default from settings)
            min_chunk_size: Minimum chunk size to avoid tiny chunks
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.min_chunk_size = min_chunk_size
        
        logger.info(
            "Initialized SemanticTextSplitter",
            extra=log_extra(
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap
            )
        )
    
    def _calculate_quality_score(self, text: str) -> float:
        """
        Calculate quality score for a chunk (0-1)
        
        Signals:
        - Text length (optimal: 100-500 words)
        - Alphabetic content ratio
        - Has numeric content (good for budget data)
        - Average word length (filters gibberish)
        """
        if not text:
            return 0.0
        
        score = 1.0
        
        # 1. Length penalty/bonus
        word_count = len(text.split())
        if word_count < 20:
            score *= 0.5  # Too short
        elif word_count < 50:
            score *= 0.8  # Short but acceptable
        elif word_count > 600:
            score *= 0.9  # Very long, might be too broad
        
        # 2. Alphabetic content
        alpha_chars = sum(1 for c in text if c.isalpha())
        alpha_ratio = alpha_chars / len(text) if len(text) > 0 else 0
        if alpha_ratio < 0.4:
            score *= 0.6  # Likely OCR noise or tables
        elif alpha_ratio > 0.8:
            score *= 1.0  # Good text
        
        # 3. Has numbers (good for budget data)
        has_numbers = any(c.isdigit() for c in text)
        if has_numbers:
            score = min(1.0, score * 1.1)  # Slight bonus
        
        # 4. Average word length (detect gibberish)
        words = text.split()
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len < 2 or avg_word_len > 20:
                score *= 0.7  # Suspicious
        
        return round(min(1.0, max(0.0, score)), 3)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)
        1 token ≈ 4 characters for English text
        """
        return len(text) // 4
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using smart regex
        Handles common abbreviations
        """
        # Common abbreviations that shouldn't split
        text = re.sub(r'\bDr\.', 'Dr', text)
        text = re.sub(r'\bMr\.', 'Mr', text)
        text = re.sub(r'\bMrs\.', 'Mrs', text)
        text = re.sub(r'\bMs\.', 'Ms', text)
        text = re.sub(r'\bNo\.', 'No', text)
        text = re.sub(r'\bvs\.', 'vs', text)
        text = re.sub(r'\betc\.', 'etc', text)
        text = re.sub(r'\bi\.e\.', 'ie', text)
        text = re.sub(r'\be\.g\.', 'eg', text)
        
        # Split on sentence boundaries
        # Look for: . ! ? followed by space and capital letter or number
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
        
        # Restore abbreviations
        sentences = [s.replace('Dr ', 'Dr. ')
                       .replace('Mr ', 'Mr. ')
                       .replace('Mrs ', 'Mrs. ')
                       .replace('Ms ', 'Ms. ')
                       .replace('No ', 'No. ')
                       .replace('vs ', 'vs. ')
                       .replace('etc ', 'etc. ')
                       .replace('ie ', 'i.e. ')
                       .replace('eg ', 'e.g. ')
                     for s in sentences]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunks_from_sentences(
        self,
        sentences: List[str]
    ) -> List[str]:
        """
        Combine sentences into chunks respecting size limits and overlap
        """
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)
            
            # If adding this sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_tokens = 0
                overlap_sentences = []
                
                for sent in reversed(current_chunk):
                    sent_tokens = self._estimate_tokens(sent)
                    if overlap_tokens + sent_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            # Only add if it meets minimum size
            if self._estimate_tokens(chunk_text) >= self.min_chunk_size // 4:
                chunks.append(chunk_text)
        
        return chunks
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into semantic chunks
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        # Clean up text
        text = text.strip()
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # Create chunks from sentences
        chunks = self._create_chunks_from_sentences(sentences)
        
        return chunks
    
    def chunk_page(
        self,
        document_name: str,
        page_number: int,
        page_text: str,
        start_chunk_index: int = 0
    ) -> List[TextChunk]:
        """
        Chunk a single page into TextChunk objects
        
        Args:
            document_name: Name of source document
            page_number: Page number in document
            page_text: Text content of page
            start_chunk_index: Starting index for chunks
            
        Returns:
            List of TextChunk objects
        """
        text_chunks = self.split_text(page_text)
        
        result = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_index = start_chunk_index + i
            chunk_id = f"{document_name}_p{page_number}_c{chunk_index}"
            
            chunk = TextChunk(
                chunk_id=chunk_id,
                document_name=document_name,
                page_number=page_number,
                chunk_index=chunk_index,
                text=chunk_text,
                char_count=len(chunk_text),
                word_count=len(chunk_text.split()),
                token_count=self._estimate_tokens(chunk_text),
                quality_score=self._calculate_quality_score(chunk_text)
            )
            
            result.append(chunk)
        
        return result
    
    def chunk_document(
        self,
        pdf_document
    ) -> List[TextChunk]:
        """
        Chunk an entire PDF document
        
        Args:
            pdf_document: PDFDocument object from pdf_loader
            
        Returns:
            List of all TextChunk objects from document
        """
        logger.info(
            f"Chunking document: {pdf_document.filename}",
            extra=log_extra(
                pages=pdf_document.total_pages,
                total_words=pdf_document.metadata['total_words']
            )
        )
        
        all_chunks = []
        chunk_counter = 0
        
        for page in pdf_document.pages:
            page_chunks = self.chunk_page(
                document_name=pdf_document.filename,
                page_number=page.page_number,
                page_text=page.text,
                start_chunk_index=chunk_counter
            )
            
            all_chunks.extend(page_chunks)
            chunk_counter += len(page_chunks)
        
        logger.info(
            f"Document chunking completed: {pdf_document.filename}",
            extra=log_extra(
                chunks_created=len(all_chunks),
                avg_chunk_words=sum(c.word_count for c in all_chunks) // len(all_chunks) if all_chunks else 0
            )
        )
        
        return all_chunks


# Convenience function
def chunk_documents(pdf_documents: List) -> Dict[str, List[TextChunk]]:
    """
    Chunk multiple PDF documents
    
    Args:
        pdf_documents: List of PDFDocument objects
        
    Returns:
        Dictionary mapping filename to list of chunks
    """
    splitter = SemanticTextSplitter()
    
    result = {}
    total_chunks = 0
    
    for doc in pdf_documents:
        chunks = splitter.chunk_document(doc)
        result[doc.filename] = chunks
        total_chunks += len(chunks)
    
    logger.info(
        "Batch chunking completed",
        extra=log_extra(
            documents=len(pdf_documents),
            total_chunks=total_chunks,
            avg_chunks_per_doc=total_chunks // len(pdf_documents) if pdf_documents else 0
        )
    )
    
    return result


if __name__ == "__main__":
    # Test the splitter
    from ..ingestion.pdf_loader import load_budget_documents
    
    print("🔪 Testing Text Splitter\n")
    
    # Load documents
    docs = load_budget_documents()
    
    if docs:
        # Test on first document
        test_doc = docs[0]
        print(f"Chunking: {test_doc.filename}")
        
        splitter = SemanticTextSplitter()
        chunks = splitter.chunk_document(test_doc)
        
        print(f"\n✅ Created {len(chunks)} chunks")
        print(f"Avg chunk size: {sum(c.word_count for c in chunks) // len(chunks)} words")
        
        # Show sample
        print(f"\nSample chunk:")
        print(f"ID: {chunks[0].chunk_id}")
        print(f"Text: {chunks[0].text[:200]}...")

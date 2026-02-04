"""
Complete ingestion pipeline for Budget 2026 AI Platform
Orchestrates: PDF Loading → Text Chunking → Metadata Tagging → Storage
"""
import json
from pathlib import Path
from typing import List, Dict,Optional
from datetime import datetime

from .pdf_loader import PDFLoader, load_budget_documents
from .text_splitter import SemanticTextSplitter, chunk_documents
from .metadata_tagger import MetadataTagger, tag_document_chunks
from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


class IngestionPipeline:
    """
    Complete ingestion pipeline that processes PDFs into tagged chunks
    """
    
    def __init__(self):
        """Initialize pipeline components"""
        self.pdf_loader = PDFLoader()
        self.text_splitter = SemanticTextSplitter()
        self.metadata_tagger = MetadataTagger()
        
        logger.info("Initialized IngestionPipeline")
    
    def process_documents(
        self,
        save_output: bool = True,
        output_format: str = 'json'
    ) -> Dict[str, any]:
        """
        Run complete pipeline: load → chunk → tag → save
        
        Args:
            save_output: Whether to save processed chunks to disk
            output_format: 'json' or 'jsonl'
            
        Returns:
            Dictionary with processing results and statistics
        """
        logger.info("=" * 70)
        logger.info("Starting complete ingestion pipeline")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        
        # Step 1: Load PDFs
        logger.info("\n📄 STEP 1: Loading PDF documents...")
        pdf_documents = self.pdf_loader.load_all_pdfs()
        
        if not pdf_documents:
            logger.error("No PDFs loaded. Pipeline aborted.")
            return None
        
        logger.info(
            f"✓ Loaded {len(pdf_documents)} documents",
            extra=log_extra(
                total_pages=sum(doc.total_pages for doc in pdf_documents),
                total_words=sum(doc.metadata['total_words'] for doc in pdf_documents)
            )
        )
        
        # Step 2: Chunk documents
        logger.info("\n🔪 STEP 2: Chunking documents into semantic pieces...")
        chunks_by_doc = {}
        
        for doc in pdf_documents:
            chunks = self.text_splitter.chunk_document(doc)
            chunks_by_doc[doc.filename] = chunks
        
        total_chunks = sum(len(chunks) for chunks in chunks_by_doc.values())
        avg_chunk_size = sum(
            sum(c.word_count for c in chunks) 
            for chunks in chunks_by_doc.values()
        ) // total_chunks if total_chunks > 0 else 0
        
        logger.info(
            f"✓ Created {total_chunks} chunks",
            extra=log_extra(
                total_chunks=total_chunks,
                avg_chunk_words=avg_chunk_size,
                chunks_per_doc={k: len(v) for k, v in chunks_by_doc.items()}
            )
        )
        
        # Step 3: Tag with metadata
        logger.info("\n🏷️  STEP 3: Tagging chunks with metadata...")
        tagged_chunks_by_doc = {}
        
        for filename, chunks in chunks_by_doc.items():
            tagged = self.metadata_tagger.tag_chunks(chunks)
            tagged_chunks_by_doc[filename] = tagged
        
        # Collect statistics
        all_topics = set()
        all_user_types = set()
        all_sectors = set()
        all_income_ranges = set()
        
        for tagged_chunks in tagged_chunks_by_doc.values():
            for chunk in tagged_chunks:
                meta = chunk['metadata']
                # Extract main topics from hierarchical structure
                for topic in meta['topics']:
                    if isinstance(topic, dict):
                        all_topics.add(topic.get('main', 'General'))
                    else:
                        all_topics.add(topic)  # Fallback for flat topics
                
                all_user_types.update(meta['user_types'])
                all_sectors.update(meta['sectors'])
                all_income_ranges.update(meta['income_ranges'])
        
        logger.info(
            f"✓ Tagged {total_chunks} chunks",
            extra=log_extra(
                unique_topics=len(all_topics),
                unique_user_types=len(all_user_types),
                unique_sectors=len(all_sectors),
                unique_income_ranges=len(all_income_ranges)
            )
        )
        
        # Step 4: Save output
        if save_output:
            logger.info("\n💾 STEP 4: Saving processed chunks...")
            output_dir = settings.OUTPUT_DIR / "processed_chunks"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if output_format == 'json':
                # Save as single JSON file
                output_file = output_dir / "budget_chunks.json"
                
                # Flatten all chunks
                all_chunks = []
                for tagged_chunks in tagged_chunks_by_doc.values():
                    all_chunks.extend(tagged_chunks)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': {
                            'created_at': datetime.now().isoformat(),
                            'total_documents': len(pdf_documents),
                            'total_chunks': len(all_chunks),
                            'topics': sorted(list(all_topics)),
                            'user_types': sorted(list(all_user_types)),
                            'sectors': sorted(list(all_sectors)),
                            'income_ranges': sorted(list(all_income_ranges))
                        },
                        'chunks': all_chunks
                    }, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✓ Saved to {output_file}")
            
            elif output_format == 'jsonl':
                # Save as JSONL (one chunk per line)
                output_file = output_dir / "budget_chunks.jsonl"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    for tagged_chunks in tagged_chunks_by_doc.values():
                        for chunk in tagged_chunks:
                            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                
                logger.info(f"✓ Saved to {output_file}")
            
            # Also save per-document files for inspection
            for filename, tagged_chunks in tagged_chunks_by_doc.items():
                doc_file = output_dir / f"{Path(filename).stem}_chunks.json"
                with open(doc_file, 'w', encoding='utf-8') as f:
                    json.dump(tagged_chunks, f, indent=2, ensure_ascii=False)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Final summary
        result = {
            'success': True,
            'documents_processed': len(pdf_documents),
            'total_pages': sum(doc.total_pages for doc in pdf_documents),
            'total_chunks': total_chunks,
            'avg_chunk_size_words': avg_chunk_size,
            'processing_time_seconds': round(processing_time, 2),
            'unique_topics': sorted(list(all_topics)),
            'unique_user_types': sorted(list(all_user_types)),
            'unique_sectors': sorted(list(all_sectors)),
            'unique_income_ranges': sorted(list(all_income_ranges)),
            'output_saved': save_output,
            'output_format': output_format if save_output else None
        }
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(
            "Final Statistics",
            extra=log_extra(**result)
        )
        
        return result


def run_ingestion_pipeline(save_output: bool = True) -> Dict:
    """
    Convenience function to run the complete pipeline
    
    Args:
        save_output: Whether to save processed chunks
        
    Returns:
        Processing results dictionary
    """
    pipeline = IngestionPipeline()
    return pipeline.process_documents(save_output=save_output)


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Budget 2026 AI - Complete Ingestion Pipeline")
    print("=" * 70)
    print()
    
    # Run pipeline
    results = run_ingestion_pipeline(save_output=True)
    
    if results:
        print("\n" + "=" * 70)
        print("📊 PROCESSING SUMMARY")
        print("=" * 70)
        print(f"Documents Processed: {results['documents_processed']}")
        print(f"Total Pages: {results['total_pages']}")
        print(f"Total Chunks: {results['total_chunks']}")
        print(f"Avg Chunk Size: {results['avg_chunk_size_words']} words")
        print(f"Processing Time: {results['processing_time_seconds']}s")
        print()
        print(f"Unique Topics: {len(results['unique_topics'])}")
        print(f"  → {', '.join(results['unique_topics'])}")
        print()
        print(f"Unique User Types: {len(results['unique_user_types'])}")
        if results['unique_user_types']:
            print(f"  → {', '.join(results['unique_user_types'])}")
        print()
        print(f"Unique Sectors: {len(results['unique_sectors'])}")
        if results['unique_sectors']:
            print(f"  → {', '.join(results['unique_sectors'])}")
        print()
        print("=" * 70)
        print("✅ Output saved to: backend/output/processed_chunks/")
        print("=" * 70)

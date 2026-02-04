#!/usr/bin/env python3
"""
Upload processed chunks to Supabase with LOCAL embeddings (100% free)
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.embeddings_local import LocalEmbeddingGenerator
from app.rag.vector_store import SupabaseVectorStore
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


def upload_to_supabase():
    """
    Complete Phase 3 pipeline with LOCAL embeddings:
    1. Load processed chunks
    2. Generate embeddings locally (FREE)
    3. Upload to Supabase
    """
    print("=" * 70)
    print("🚀 Phase 3: Upload to Supabase with Local Embeddings")
    print("=" * 70)
    print()
    
    # Check configuration
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("❌ Supabase credentials not set")
        print("Check your .env file")
        return False
    
    # Load chunks
    chunks_file = settings.OUTPUT_DIR / "processed_chunks" / "budget_chunks.json"
    
    if not chunks_file.exists():
        print(f"❌ Chunks file not found: {chunks_file}")
        print("Run: python test_phase2_pipeline.py first")
        return False
    
    print(f"📁 Loading chunks from: {chunks_file}")
    with open(chunks_file, 'r') as f:
        data = json.load(f)
    
    chunks = data['chunks']
    print(f"✓ Loaded {len(chunks)} chunks")
    print()
    
    # Step 1: Generate embeddings locally
    print("🔮 Step 1/3: Generating embeddings locally...")
    print(f"   Model: sentence-transformers/all-MiniLM-L6-v2")
    print(f"   Dimensions: 384")
    print(f"   Cost: FREE (runs on your CPU)")
    print()
    
    generator = LocalEmbeddingGenerator()
    start_time = datetime.now()
    
    embedded_chunks = generator.embed_chunks(chunks, batch_size=32)
    
    embedding_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ Generated embeddings in {embedding_time:.1f}s")
    print()
    
    # Save embedded chunks locally
    embedded_file = settings.OUTPUT_DIR / "processed_chunks" / "budget_chunks_embedded.json"
    print(f"💾 Saving embedded chunks to: {embedded_file}")
    
    with open(embedded_file, 'w') as f:
        json.dump({
            'metadata': data.get('metadata', {}),
            'chunks': embedded_chunks
        }, f)
    
    print(f"✓ Saved {len(embedded_chunks)} embedded chunks")
    print()
    
    # Step 2: Initialize Supabase
    print("🗄️  Step 2/3: Connecting to Supabase...")
    print(f"   URL: {settings.SUPABASE_URL}")
    print(f"   Table: {settings.SUPABASE_TABLE}")
    print()
    
    store = SupabaseVectorStore()
    
    # Check if table exists
    try:
        count = store.get_chunk_count()
        print(f"✓ Connected! Current chunks in database: {count}")
        
        if count > 0:
            print(f"\n⚠️  WARNING: Database already has {count} chunks")
            response = input("Delete existing chunks and re-upload? (yes/no): ")
            if response.lower() == 'yes':
                store.delete_all_chunks()
                print("✓ Existing chunks deleted")
            else:
                print("Skipping upload. Existing chunks will remain.")
                return True
    except Exception as e:
        print(f"✓ Table is ready (empty)")
    
    print()
    
    # Step 3: Upload chunks
    print("📤 Step 3/3: Uploading chunks to Supabase...")
    print(f"   Batch size: 100 chunks")
    print()
    
    upload_start = datetime.now()
    stats = store.upload_chunks_batch(embedded_chunks, batch_size=100)
    upload_time = (datetime.now() - upload_start).total_seconds()
    
    print()
    print("=" * 70)
    print("📊 UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Total chunks: {stats['total']}")
    print(f"Uploaded: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Upload time: {upload_time:.1f}s")
    print(f"Embedding time: {embedding_time:.1f}s")
    print(f"Total time: {embedding_time + upload_time:.1f}s")
    print()
    
    if stats['failed'] == 0:
        print("✅ All chunks uploaded successfully!")
        print(f"🎉 Phase 3 complete! {stats['success']} chunks ready for search")
        print()
        print("Next: Test similarity search")
        print("  python scripts/test_search_local.py")
        return True
    else:
        print(f"⚠️  {stats['failed']} chunks failed to upload")
        print("Check logs for details")
        return False


if __name__ == "__main__":
    success = upload_to_supabase()
    sys.exit(0 if success else 1)

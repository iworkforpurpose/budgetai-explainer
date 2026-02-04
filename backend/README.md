# Budget 2026 AI Explainer - Backend

Production-grade RAG system for understanding India's Union Budget 2026.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Test PDF Loading (Phase 1)

```bash
python test_pdf_loader.py
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   └── logger.py          # Structured logging
│   ├── ingestion/             # Phase 1: PDF Processing
│   │   ├── pdf_loader.py      # PDF extraction (PyMuPDF + pdfplumber)
│   │   ├── text_splitter.py   # Text chunking (Phase 2)
│   │   └── metadata_tagger.py # Metadata enrichment (Phase 2)
│   ├── rag/                   # RAG System
│   │   ├── embeddings.py      # Sentence transformers
│   │   ├── vector_store.py    # FAISS/Pinecone
│   │   ├── retriever.py       # Similarity search
│   │   └── prompt_templates.py
│   └── api/                   # FastAPI endpoints
│       ├── chat.py
│       ├── documents.py
│       └── analytics.py
├── documents/                 # Budget PDFs (6 documents)
├── output/                    # Processed data & vector indexes
├── logs/                      # Application logs
├── requirements.txt
├── .env.example
└── test_pdf_loader.py
```

## 📊 Phase 1: PDF Ingestion Pipeline ✅

### Features Implemented

- ✅ **Dual PDF Extraction**: PyMuPDF (primary) + pdfplumber (fallback)
- ✅ **Production-Safe**: File validation, size checks, error handling
- ✅ **Metadata Capture**: Pages, words, tables, images, file hash
- ✅ **Structured Logging**: JSON/text format with detailed tracking
- ✅ **Batch Processing**: Load all PDFs from documents folder
- ✅ **Performance Tracking**: Processing time per document

### Documents Loaded

1. `Budget_Speech.pdf` - Finance Minister's budget speech
2. `Finance_Bill.pdf` - Detailed tax and finance provisions
3. `budget_at_a_glance.pdf` - High-level summary
4. `demands_for_grants2026.pdf` - Ministry-wise allocations
5. `expenditure_profile2026.pdf` - Spending breakdown
6. `reciepts_profile_full.pdf` - Revenue and receipts

### Output Structure

Each PDF is converted to a `PDFDocument` object containing:

```python
PDFDocument(
    filename="Budget_Speech.pdf",
    file_path="/path/to/file",
    file_size_mb=0.65,
    total_pages=58,
    pages=[
        PageContent(
            page_number=1,
            text="...",
            char_count=2156,
            word_count=347,
            has_tables=True,
            has_images=False
        ),
        # ... more pages
    ],
    extraction_method="pymupdf",
    processing_time_seconds=1.23,
    file_hash="a7f5c...",
    extracted_at="2026-02-04T22:30:00",
    metadata={
        "total_chars": 125348,
        "total_words": 20145,
        "pages_with_images": 12,
        "pages_with_tables": 45
    }
)
```

## 🔧 Configuration

Key settings in `.env`:

```env
# PDF Processing
MAX_PDF_SIZE_MB=50
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384

# Vector Store
VECTOR_STORE_TYPE=faiss  # or pinecone
```

## 📝 Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `logs/budget_ai_YYYYMMDD.log`

Format: JSON (structured) or Text (human-readable)

## 🧪 Testing

Run the test script:

```bash
python test_pdf_loader.py
```

Expected output:
```
✅ Successfully loaded 6 documents

1. 📄 Budget_Speech.pdf
   └─ Pages: 58
   └─ Words: 20,145
   └─ Size: 0.65 MB
   └─ Extraction Method: pymupdf
   └─ Processing Time: 1.23s
   ...
```

## 🎯 Next Steps (Phase 2)

- [ ] Text chunking with semantic splitting
- [ ] Metadata tagging (topic, user_type, sector, income_range)
- [ ] Embedding generation
- [ ] Vector store indexing

## 🐛 Troubleshooting

### PDFs not loading?

1. Check PDFs exist in `backend/documents/`
2. Verify PDF files are not corrupted
3. Check logs in `backend/logs/`

### Import errors?

```bash
pip install -r requirements.txt
```

### Permission errors?

```bash
chmod +x test_pdf_loader.py
```

## 📚 Dependencies

See `requirements.txt` for full list.

Key libraries:
- **PyMuPDF** (fitz) - Fast PDF text extraction
- **pdfplumber** - Complex layout handling
- **pydantic** - Configuration validation
- **sentence-transformers** - Embeddings (Phase 2)
- **FAISS** - Vector similarity search (Phase 2)

"""
Production-grade PDF loader for Budget 2026 AI Platform
Extracts text from PDF documents with robust error handling and metadata capture
"""
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

from ..core.config import settings
from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


@dataclass
class PageContent:
    """Represents content from a single PDF page"""
    page_number: int
    text: str
    char_count: int
    word_count: int
    has_tables: bool = False
    has_images: bool = False


@dataclass
class PDFDocument:
    """Represents a complete PDF document with metadata"""
    filename: str
    file_path: str
    file_size_mb: float
    total_pages: int
    pages: List[PageContent]
    extraction_method: str
    processing_time_seconds: float
    file_hash: str
    extracted_at: str
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)


class PDFLoader:
    """
    Production-safe PDF loader with fallback mechanisms
    
    Primary: PyMuPDF (fast, accurate)
    Fallback: pdfplumber (better for complex layouts)
    """
    
    def __init__(self, documents_dir: Optional[Path] = None):
        """
        Initialize PDF loader
        
        Args:
            documents_dir: Directory containing PDF files. Defaults to settings.DOCUMENTS_DIR
        """
        self.documents_dir = documents_dir or settings.DOCUMENTS_DIR
        logger.info(
            f"Initialized PDFLoader",
            extra=log_extra(documents_dir=str(self.documents_dir))
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity checking"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _validate_pdf(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file before processing
        
        Returns:
            (is_valid, error_message)
        """
        # Check file exists
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Check file extension
        if file_path.suffix.lower() not in settings.SUPPORTED_PDF_EXTENSIONS:
            return False, f"Unsupported file type: {file_path.suffix}"
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.MAX_PDF_SIZE_MB:
            return False, f"File too large: {file_size_mb:.2f}MB (max: {settings.MAX_PDF_SIZE_MB}MB)"
        
        # Try to open with PyMuPDF to verify it's a valid PDF
        try:
            doc = fitz.open(file_path)
            doc.close()
        except Exception as e:
            return False, f"Invalid or corrupted PDF: {str(e)}"
        
        return True, None
    
    def _extract_with_pymupdf(self, file_path: Path) -> List[PageContent]:
        """
        Extract text using PyMuPDF (primary method)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of PageContent objects
        """
        pages = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                text = page.get_text("text")
                
                # Get metadata
                has_images = len(page.get_images()) > 0
                
                # Create page content
                page_content = PageContent(
                    page_number=page_num + 1,  # 1-indexed
                    text=text,
                    char_count=len(text),
                    word_count=len(text.split()),
                    has_images=has_images,
                    has_tables=False  # PyMuPDF doesn't detect tables easily
                )
                
                pages.append(page_content)
            
            doc.close()
            logger.debug(
                f"PyMuPDF extraction successful",
                extra=log_extra(file=file_path.name, pages=len(pages))
            )
            
        except Exception as e:
            logger.error(
                f"PyMuPDF extraction failed: {str(e)}",
                extra=log_extra(file=file_path.name),
                exc_info=True
            )
            raise
        
        return pages
    
    def _extract_with_pdfplumber(self, file_path: Path) -> List[PageContent]:
        """
        Extract text using pdfplumber (fallback method)
        Better for complex layouts and table detection
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of PageContent objects
        """
        pages = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    text = page.extract_text() or ""
                    
                    # Detect tables
                    tables = page.extract_tables()
                    has_tables = len(tables) > 0
                    
                    # Detect images
                    has_images = len(page.images) > 0
                    
                    # Create page content
                    page_content = PageContent(
                        page_number=page_num + 1,
                        text=text,
                        char_count=len(text),
                        word_count=len(text.split()),
                        has_tables=has_tables,
                        has_images=has_images
                    )
                    
                    pages.append(page_content)
            
            logger.debug(
                f"pdfplumber extraction successful",
                extra=log_extra(file=file_path.name, pages=len(pages))
            )
            
        except Exception as e:
            logger.error(
                f"pdfplumber extraction failed: {str(e)}",
                extra=log_extra(file=file_path.name),
                exc_info=True
            )
            raise
        
        return pages
    
    def load_pdf(
        self,
        file_path: Path,
        use_fallback: bool = True
    ) -> Optional[PDFDocument]:
        """
        Load and extract text from a single PDF file
        
        Args:
            file_path: Path to PDF file
            use_fallback: Whether to use pdfplumber if PyMuPDF fails
            
        Returns:
            PDFDocument object or None if extraction fails
        """
        start_time = datetime.now()
        
        logger.info(
            f"Starting PDF extraction",
            extra=log_extra(file=file_path.name)
        )
        
        # Validate PDF
        is_valid, error_msg = self._validate_pdf(file_path)
        if not is_valid:
            logger.error(
                f"PDF validation failed: {error_msg}",
                extra=log_extra(file=file_path.name)
            )
            return None
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Extract text - try PyMuPDF first
        extraction_method = "pymupdf"
        pages = None
        
        try:
            pages = self._extract_with_pymupdf(file_path)
        except Exception as e:
            logger.warning(
                f"PyMuPDF failed, attempting fallback",
                extra=log_extra(file=file_path.name, error=str(e))
            )
            
            if use_fallback:
                try:
                    extraction_method = "pdfplumber"
                    pages = self._extract_with_pdfplumber(file_path)
                except Exception as fallback_error:
                    logger.error(
                        f"Both extraction methods failed",
                        extra=log_extra(
                            file=file_path.name,
                            pymupdf_error=str(e),
                            pdfplumber_error=str(fallback_error)
                        ),
                        exc_info=True
                    )
                    return None
            else:
                return None
        
        if not pages:
            logger.error(
                f"No pages extracted",
                extra=log_extra(file=file_path.name)
            )
            return None
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Create PDF document object
        pdf_doc = PDFDocument(
            filename=file_path.name,
            file_path=str(file_path),
            file_size_mb=round(file_size_mb, 2),
            total_pages=len(pages),
            pages=pages,
            extraction_method=extraction_method,
            processing_time_seconds=round(processing_time, 2),
            file_hash=file_hash,
            extracted_at=datetime.now().isoformat(),
            metadata={
                "total_chars": sum(p.char_count for p in pages),
                "total_words": sum(p.word_count for p in pages),
                "pages_with_images": sum(1 for p in pages if p.has_images),
                "pages_with_tables": sum(1 for p in pages if p.has_tables),
            }
        )
        
        logger.info(
            f"PDF extraction completed successfully",
            extra=log_extra(
                file=file_path.name,
                pages=len(pages),
                method=extraction_method,
                time=processing_time,
                words=pdf_doc.metadata["total_words"]
            )
        )
        
        return pdf_doc
    
    def load_all_pdfs(self) -> List[PDFDocument]:
        """
        Load all PDF files from documents directory
        
        Returns:
            List of successfully loaded PDFDocument objects
        """
        logger.info(
            f"Starting batch PDF loading",
            extra=log_extra(directory=str(self.documents_dir))
        )
        
        # Find all PDF files
        pdf_files = list(self.documents_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(
                f"No PDF files found",
                extra=log_extra(directory=str(self.documents_dir))
            )
            return []
        
        logger.info(
            f"Found PDF files",
            extra=log_extra(count=len(pdf_files))
        )
        
        # Load each PDF
        documents = []
        failed_files = []
        
        for pdf_file in pdf_files:
            pdf_doc = self.load_pdf(pdf_file)
            
            if pdf_doc:
                documents.append(pdf_doc)
            else:
                failed_files.append(pdf_file.name)
        
        # Summary logging
        logger.info(
            f"Batch PDF loading completed",
            extra=log_extra(
                total_files=len(pdf_files),
                successful=len(documents),
                failed=len(failed_files),
                failed_files=failed_files
            )
        )
        
        return documents


# Convenience function for quick loading
def load_budget_documents() -> List[PDFDocument]:
    """
    Quick helper to load all Budget 2026 documents
    
    Returns:
        List of PDFDocument objects
    """
    loader = PDFLoader()
    return loader.load_all_pdfs()


if __name__ == "__main__":
    # Test the loader
    print("🚀 Budget 2026 PDF Loader - Test Run\n")
    
    loader = PDFLoader()
    documents = loader.load_all_pdfs()
    
    print(f"\n✅ Loaded {len(documents)} documents:\n")
    
    for doc in documents:
        print(f"📄 {doc.filename}")
        print(f"   Pages: {doc.total_pages}")
        print(f"   Words: {doc.metadata['total_words']:,}")
        print(f"   Size: {doc.file_size_mb} MB")
        print(f"   Method: {doc.extraction_method}")
        print(f"   Time: {doc.processing_time_seconds}s")
        print()

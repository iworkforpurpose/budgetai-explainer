"""
Configuration management for Budget 2026 AI Platform
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Project Info
    PROJECT_NAME: str = "Budget 2026 AI Explainer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DOCUMENTS_DIR: Path = BASE_DIR / "documents"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # PDF Processing
    MAX_PDF_SIZE_MB: int = 50
    SUPPORTED_PDF_EXTENSIONS: list = [".pdf"]
    
    # Text Processing
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Embeddings (100% Free - Local Model)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_PROVIDER: str = "local"  # local (free) or openai (paid)
    VECTOR_DIMENSION: int = 384  # 384 for local, 1536 for OpenAI
    
    # Supabase (Production Vector Store)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_TABLE: str = "budget_chunks"
    
    # OpenAI API (for embeddings)
    OPENAI_API_KEY: str = ""
    
    # LLM Configuration (Hybrid Approach)
    LLM_PROVIDER: str = "groq"  # groq, openai, or anthropic
    LLM_MODEL: str = "llama-3.1-8b-instant"  # Groq model
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024
    
    # Groq API (for LLM - recommended)
    GROQ_API_KEY: str = ""
    
    # Anthropic API (optional)
    ANTHROPIC_API_KEY: str = ""
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"  # faiss or chromadb
    FAISS_INDEX_PATH: Path = OUTPUT_DIR / "faiss_index"
    
    # API Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # LLM API Keys
    LLM_API_KEY: str = ""  # Generic key for selected provider
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

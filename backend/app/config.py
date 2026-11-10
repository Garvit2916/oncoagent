"""
Central configuration for OncoAgent backend.
Loads settings from environment variables with safe defaults.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Application
    APP_NAME: str = "OncoAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    
    # LLM Provider: gemini (free tier) or ollama (local)
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    
    # RAG / Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_TOP_K: int = 4
    RAG_INDEX_DIR: str = str(BASE_DIR / "backend" / "rag_index")
    
    # PubMed
    PUBMED_EMAIL: str = "oncoagent@example.com"
    PUBMED_MAX_RESULTS: int = 10
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'backend' / 'oncoagent.db'}"
    
    # Model paths
    YOLO_MODEL_PATH: str = str(BASE_DIR / "backend" / "models" / "yolo_best.pt")
    UNET_MODEL_PATH: str = str(BASE_DIR / "backend" / "models" / "unet_best.pth")
    SYMPTOM_MODEL_PATH: str = str(BASE_DIR / "backend" / "models" / "lung_cancer_ultra_model_v3.pkl")
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".bmp", ".nii", ".nii.gz"}
    
    @property
    def is_gemini_available(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.LLM_PROVIDER == "gemini")
    
    @property
    def is_ollama_available(self) -> bool:
        return self.LLM_PROVIDER == "ollama"


settings = Settings()

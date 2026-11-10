"""Embedding utilities for RAG pipeline using sentence-transformers."""

import numpy as np
from typing import List, Optional
import logging
from backend.app.config import settings
from backend.app.utils.logger import logger


class Embedder:
    """Text embedding using sentence-transformers (local, free)."""
    
    def __init__(self):
        self._model = None
        self.model_name = settings.EMBEDDING_MODEL
    
    def _load_model(self):
        """Load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        self._load_model()
        if not texts:
            return np.array([])
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.embed([text])[0]
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
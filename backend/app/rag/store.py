"""FAISS vector store for RAG pipeline."""

import faiss
import numpy as np
import pickle
import os
from typing import List, Optional
from backend.app.config import settings
from backend.app.utils.logger import logger


class VectorStore:
    """FAISS-based vector store for medical literature."""
    
    def __init__(self, index_path: str = None):
        self.index_path = index_path or settings.RAG_INDEX_DIR
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self.index = None
        self.documents = []
        self._initialized = False
    
    def initialize(self):
        """Initialize FAISS index."""
        if self._initialized:
            return
        
        # Create directory if needed
        os.makedirs(self.index_path, exist_ok=True)
        
        # Create FAISS index with inner product (cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.dimension)
        self._initialized = True
        logger.info(f"✅ FAISS index initialized (dimension={self.dimension})")
    
    def add_documents(self, documents: List[dict], embeddings: np.ndarray):
        """Add documents and their embeddings to the store."""
        self.initialize()
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        self.index.add(embeddings.astype(np.float32))
        self.documents.extend(documents)
        
        logger.info(f"✅ Added {len(documents)} documents to FAISS store")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 4) -> List[dict]:
        """Search for similar documents."""
        self.initialize()
        
        if self.index.ntotal == 0:
            return []
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
        
        return results
    
    def save(self):
        """Save FAISS index and documents to disk."""
        self.initialize()
        
        # Save FAISS index
        index_path = os.path.join(self.index_path, "faiss_index.bin")
        faiss.write_index(self.index, index_path)
        
        # Save documents
        docs_path = os.path.join(self.index_path, "documents.pkl")
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"✅ Saved FAISS index to {index_path}")
    
    def load(self) -> bool:
        """Load FAISS index and documents from disk."""
        self.initialize()
        
        index_path = os.path.join(self.index_path, "faiss_index.bin")
        docs_path = os.path.join(self.index_path, "documents.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return False
        
        try:
            self.index = faiss.read_index(index_path)
            with open(docs_path, "rb") as f:
                self.documents = pickle.load(f)
            logger.info(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False
    
    def clear(self):
        """Clear the vector store."""
        self.initialize()
        self.index.reset()
        self.documents = []
        logger.info("✅ FAISS store cleared")
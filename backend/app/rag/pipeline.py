"""RAG pipeline for medical literature evidence grounding."""

from typing import List, Optional, Dict
from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.rag.ncbi_client import PubMedClient, PubMedPaper
from backend.app.rag.chunker import chunk_pubmed_papers
from backend.app.rag.embedder import Embedder
from backend.app.rag.store import VectorStore


class RAGPipeline:
    """End-to-end RAG pipeline for medical literature."""
    
    def __init__(self):
        self.pubmed_client = PubMedClient()
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self._initialized = False
    
    def initialize(self):
        """Initialize the RAG pipeline."""
        if self._initialized:
            return
        
        # Try to load existing index
        if self.vector_store.load():
            self._initialized = True
            logger.info("✅ RAG pipeline initialized from existing index")
            return
        
        # Initialize embedder
        self.embedder._load_model()
        self._initialized = True
        logger.info("✅ RAG pipeline initialized (empty index)")
    
    def search_literature(
        self,
        query: str,
        max_results: int = 5,
        use_cache: bool = True,
    ) -> List[PubMedPaper]:
        """Search PubMed for relevant literature."""
        self.initialize()
        
        # Construct query with cancer context
        full_query = f"{query} cancer treatment diagnosis"
        
        logger.info(f"🔍 Searching PubMed: {full_query}")
        papers = self.pubmed_client.search_and_fetch(
            full_query, max_results=max_results
        )
        
        logger.info(f"✅ Found {len(papers)} papers")
        return papers
    
    def add_papers_to_index(self, papers: List[PubMedPaper]):
        """Add papers to the vector store."""
        self.initialize()
        
        if not papers:
            return
        
        # Chunk papers
        chunks = chunk_pubmed_papers(papers)
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedder.embed(texts)
        
        # Add to store
        self.vector_store.add_documents(chunks, embeddings)
        self.vector_store.save()
        
        logger.info(f"✅ Indexed {len(chunks)} chunks from {len(papers)} papers")
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 4,
    ) -> List[dict]:
        """Retrieve relevant context from vector store."""
        self.initialize()
        
        # Generate query embedding
        query_embedding = self.embedder.embed_single(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        logger.info(f"✅ Retrieved {len(results)} relevant chunks")
        return results
    
    def search_and_retrieve(
        self,
        query: str,
        max_results: int = 5,
        top_k: int = 4,
    ) -> List[dict]:
        """Search PubMed and retrieve relevant context."""
        # Search PubMed
        papers = self.search_literature(query, max_results=max_results)
        
        if not papers:
            return []
        
        # Add to index
        self.add_papers_to_index(papers)
        
        # Retrieve context
        context = self.retrieve_context(query, top_k=top_k)
        
        return context
    
    def build_evidence_report(self, context_chunks: List[dict]) -> str:
        """Build a formatted evidence report from context chunks."""
        if not context_chunks:
            return "No literature evidence available."
        
        report_parts = []
        seen_pmids = set()
        
        for chunk in context_chunks:
            pmid = chunk.get("pmid", "")
            if pmid in seen_pmids:
                continue
            seen_pmids.add(pmid)
            
            report_parts.append(
                f"**{chunk.get('title', 'Untitled')}**\n"
                f"Authors: {chunk.get('authors', 'N/A')}\n"
                f"Journal: {chunk.get('journal', 'N/A')} ({chunk.get('pub_date', 'N/A')})\n"
                f"PMID: {pmid}\n"
                f"URL: {chunk.get('url', 'N/A')}\n"
                f"Relevance: {chunk.get('score', 0):.2f}\n"
            )
        
        return "\n---\n".join(report_parts)


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
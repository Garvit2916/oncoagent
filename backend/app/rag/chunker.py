"""Text chunking utility for RAG pipeline."""

import re
from typing import List


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Chunk text into overlapping segments."""
    if not text or len(text) < chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to find sentence boundary near chunk_size
        if end < len(text):
            # Look for sentence boundary within overlap region
            search_start = start + chunk_size - overlap
            search_end = start + chunk_size + overlap
            search_end = min(search_end, len(text))
            
            sentence_boundary = text.rfind(". ", search_start, search_end)
            if sentence_boundary != -1:
                end = sentence_boundary + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end > start else end + 1
    
    return chunks


def chunk_pubmed_papers(papers, chunk_size: int = 400) -> List[dict]:
    """Chunk PubMed papers into searchable segments."""
    chunks = []
    
    for paper in papers:
        # Combine title + abstract for chunking
        text = f"{paper.title} {paper.abstract}"
        text_chunks = chunk_text(text, chunk_size=chunk_size, overlap=100)
        
        for i, chunk_text in enumerate(text_chunks):
            chunks.append({
                "pmid": paper.pmid,
                "title": paper.title,
                "authors": paper.authors,
                "journal": paper.journal,
                "pub_date": paper.pub_date,
                "url": paper.url,
                "chunk_index": i,
                "text": chunk_text,
            })
    
    return chunks
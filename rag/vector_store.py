import os
import json
import logging
import faiss
import numpy as np
from typing import List, Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, index_path: str = "faiss_index.bin", metadata_path: str = "metadata.json", dimension: int = 1536):
        """
        Initializes the VectorStore with FAISS and local metadata storage.
        """
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product on normalized vectors = Cosine Similarity
        self.chunks: List[Dict[str, Any]] = []
        
        # Load existing data on startup
        self.load()

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Applies L2 normalization to vectors for cosine similarity search."""
        faiss.normalize_L2(vectors)
        return vectors

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Adds a list of chunks with embeddings to the FAISS index and metadata storage.
        Expects chunk to have 'embedding' (List[float]), 'id', 'text', and 'metadata'.
        """
        if not chunks:
            return
        
        try:
            embeddings = [c["embedding"] for c in chunks]
            embeddings_np = np.array(embeddings).astype('float32')
            self._normalize(embeddings_np)
            
            # Store metadata without the large embedding vector to save memory
            for chunk in chunks:
                clean_chunk = chunk.copy()
                if "embedding" in clean_chunk:
                    del clean_chunk["embedding"]
                self.chunks.append(clean_chunk)
                
            self.index.add(embeddings_np)
            logger.info(f"Successfully added {len(chunks)} vectors to FAISS index. Total count: {self.index.ntotal}")
            
            # Persist to disk after adding
            self.save()
            
        except Exception as e:
            logger.error(f"Failed to add chunks to vector store: {str(e)}")
            raise e

    def search(self, query_embedding: List[float], top_k: int = 5, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Performs similarity search in FAISS.
        - query_embedding: The vector to search for.
        - top_k: Number of results to return.
        - document_id: Optional filter to restrict results to a specific document.
        """
        if self.index.ntotal == 0:
            logger.warning("Search attempted on an empty FAISS index.")
            return []

        query_np = np.array([query_embedding]).astype('float32')
        self._normalize(query_np)
        
        # If filtering, search more results first then filter manually.
        # For a massive index, we would use FAISS ID selectors, but for local/memory this is efficient.
        search_k = top_k if not document_id else max(top_k * 5, 100)
        search_k = min(search_k, self.index.ntotal)
        
        distances, indices = self.index.search(query_np, search_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: 
                continue
            
            if idx >= len(self.chunks):
                logger.error(f"FAISS index {idx} out of range for chunks metadata (len {len(self.chunks)})")
                continue
                
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(distances[0][i])
            
            # Apply document filtering if provided
            if document_id:
                if chunk.get("metadata", {}).get("document_id") == document_id:
                    results.append(chunk)
            else:
                results.append(chunk)
                
            if len(results) >= top_k:
                break
        
        logger.info(f"Search completed. Found {len(results)} matches (top_k={top_k}, doc_filter={document_id})")
        return results

    def save(self):
        """Persists the FAISS index and metadata to disk."""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
            logger.info(f"Vector store persisted to: {self.index_path} and {self.metadata_path}")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")

    def load(self):
        """Loads FAISS index and metadata from disk if they exist."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
                
                # Check for dimension mismatch
                if self.index.d != self.dimension:
                    logger.warning(f"Index dimension {self.index.d} differs from config {self.dimension}. Resetting.")
                    self.index = faiss.IndexFlatIP(self.dimension)
                    self.chunks = []
                else:
                    logger.info(f"Successfully loaded {self.index.ntotal} vectors from disk.")
                    
            except Exception as e:
                logger.error(f"Error loading vector store from disk: {str(e)}. Starting with fresh index.")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.chunks = []
        else:
            logger.info("No existing vector store found on disk. Initializing empty index.")

# Singleton instance to be shared across the application
vector_store = VectorStore()

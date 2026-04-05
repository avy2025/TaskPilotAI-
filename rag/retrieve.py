from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from .embed import generate_embeddings
from .vector_store import vector_store

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/rag", tags=["Retrieval"])

# Search request model
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    document_id: Optional[str] = None

@router.post("/search")
async def search_rag(request: SearchRequest):
    """
    Endpoint for similarity search in the document knowledge base.
    - Path: POST /api/rag/search
    - Body: { "query": "text to search", "top_k": 5, "document_id": "optional" }
    - Returns: List of most relevant document chunks
    """
    if not request.query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    logger.info(f"Received search request: '{request.query}' (top_k={request.top_k}, document_id={request.document_id})")

    try:
        # 1. Generate embedding for query
        # Reuse existing logic in embed.py
        query_embeddings = await generate_embeddings([request.query])
        if not query_embeddings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding."
            )
            
        query_embedding = query_embeddings[0]

        # 2. Perform similarity search in FAISS
        # L2 normalization is handled within vector_store.search()
        search_results = vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            document_id=request.document_id
        )

        # 3. Format response (exclude internal fields, keep text and metadata)
        formatted_results = []
        for res in search_results:
            formatted_results.append({
                "text": res.get("text", ""),
                "score": res.get("score"),
                "metadata": res.get("metadata", {})
            })

        logger.info(f"Returning {len(formatted_results)} results for query: '{request.query}'")
        return {
            "query": request.query,
            "results_count": len(formatted_results),
            "results": formatted_results
        }

    except Exception as e:
        logger.error(f"Error during retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during retrieval: {str(e)}"
        )

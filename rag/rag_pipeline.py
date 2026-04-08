import os
import time
import logging
import json
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from .embed import generate_embeddings
from .vector_store import vector_store

# Configure logger
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, model_name: str = "gemini-1.5-flash", top_k: int = 5, context_limit: int = 4000):
        self.model_name = model_name
        self.top_k = top_k
        self.context_limit = context_limit
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables.")

    async def get_relevant_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves and formats top relevant chunks from FAISS."""
        # 1. Generate embedding for query
        query_embeddings = await generate_embeddings([query])
        if not query_embeddings:
            logger.error("Failed to generate query embedding.")
            return []
        
        query_embedding = query_embeddings[0]

        # 2. Search in FAISS
        results = vector_store.search(query_embedding, top_k=self.top_k)
        return results

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Cleans and formats retrieved chunks into a single string."""
        formatted_chunks = []
        current_length = 0
        
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "").strip()
            # Simple heuristic for token limiting by character count
            if current_length + len(text) > self.context_limit:
                logger.warning(f"Context limit reached. Skipping remaining chunks. Total chars: {current_length}")
                break
                
            source = chunk.get("metadata", {}).get("source", "Unknown")
            formatted_chunks.append(f"--- SOURCE: {source} ---\n{text}")
            current_length += len(text)
            
        return "\n\n".join(formatted_chunks)

    async def generate_response(self, query: str) -> Dict[str, Any]:
        """Runs the full RAG flow: Retrieve -> Prompt -> LLM -> Response."""
        start_time = time.time()
        
        # Step 1 & 2: Retrieve context
        chunks = await self.get_relevant_context(query)
        context_text = self.format_context(chunks)
        
        # Step 3: Construct prompt
        prompt = f"""CONTEXT:
{context_text if context_text else "No relevant context found in documents."}

QUESTION:
{query}

ANSWER:"""

        # Step 4: LLM Call
        if not self.api_key:
            return {
                "answer": "Error: GEMINI_API_KEY not configured.",
                "sources": []
            }

        try:
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                api_key=self.api_key,
                temperature=0.2
            )
            
            response = await llm.ainvoke(prompt)
            answer = response.content
            
            # Prepare sources for response
            sources = []
            for res in chunks:
                sources.append({
                    "text": res.get("text", ""),
                    "metadata": res.get("metadata", {})
                })

            response_time = round(time.time() - start_time, 3)
            prompt_size = len(prompt)
            
            # Logging requirements
            logger.info(f"RAG Flow Completed:")
            logger.info(f" - Retrieved Chunks: {len(chunks)}")
            logger.info(f" - Total Prompt Size: {prompt_size} characters")
            logger.info(f" - Response Time: {response_time} seconds")
            
            return {
                "answer": answer,
                "sources": sources,
                "metrics": {
                    "chunks_retrieved": len(chunks),
                    "prompt_size": prompt_size,
                    "response_time": response_time
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RAG generation: {str(e)}")
            return {
                "answer": f"An error occurred during generation: {str(e)}",
                "sources": []
            }

# Singleton instance
rag_pipeline = RAGPipeline()

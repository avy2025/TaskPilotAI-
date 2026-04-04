import os
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Generates embeddings for a list of texts using OpenAI's API.
    
    Args:
        texts: A list of strings to embed.
        model: The OpenAI embedding model to use.
        
    Returns:
        A list of embedding vectors (list of floats).
    """
    if not texts:
        return []

    try:
        # OpenAI supports batching by passing a list of strings
        response = await client.embeddings.create(
            input=texts,
            model=model
        )
        
        # Extract embeddings and maintain order
        embeddings = [data.embedding for data in response.data]
        return embeddings
        
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # In a real app, you might want to re-raise or handle retries
        raise e

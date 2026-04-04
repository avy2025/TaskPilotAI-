import uuid
from typing import List, Dict

def chunk_text(text: str, filename: str, document_id: str, chunk_size: int = 700, overlap: int = 150) -> List[Dict]:
    """
    Splits text into chunks based on word count with a specified overlap.
    
    Args:
        text: The raw text to chunk.
        filename: Original filename for metadata.
        document_id: Unique UUID for the document.
        chunk_size: Target number of words per chunk.
        overlap: Number of overlapping words between chunks.
        
    Returns:
        A list of dictionaries containing chunk text and metadata.
    """
    words = text.split()
    chunks = []
    
    if not words:
        return []

    # If the text is smaller than the chunk size, return it as a single chunk
    if len(words) <= chunk_size:
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": " ".join(words),
            "metadata": {
                "source": filename,
                "document_id": document_id,
                "chunk_index": 0
            }
        })
        return chunks

    start = 0
    chunk_index = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        
        chunk_data = {
            "id": str(uuid.uuid4()),
            "text": " ".join(chunk_words),
            "metadata": {
                "source": filename,
                "document_id": document_id,
                "chunk_index": chunk_index
            }
        }
        chunks.append(chunk_data)
        
        # Move start by (chunk_size - overlap)
        start += (chunk_size - overlap)
        chunk_index += 1
        
        # Avoid creating a tiny chunk at the very end if we've already covered everything
        if start >= len(words):
            break
            
    return chunks

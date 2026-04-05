import sys
import os
import numpy as np
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

from rag.vector_store import VectorStore

# Mock logging
logging.basicConfig(level=logging.INFO)

def test_vector_store():
    print("--- Starting VectorStore Unit Test ---")
    
    # Initialize with temp files
    vs = VectorStore(index_path="test_faiss.bin", metadata_path="test_metadata.json", dimension=4)
    
    # 1. Test add_chunks
    chunks = [
        {
            "id": "1",
            "text": "Hello world",
            "embedding": [1.0, 0.0, 0.0, 0.0],
            "metadata": {"document_id": "doc1", "source": "test.txt"}
        },
        {
            "id": "2",
            "text": "Goodbye world",
            "embedding": [0.0, 1.0, 0.0, 0.0],
            "metadata": {"document_id": "doc1", "source": "test.txt"}
        },
        {
            "id": "3",
            "text": "Different document",
            "embedding": [0.0, 0.0, 1.0, 0.0],
            "metadata": {"document_id": "doc2", "source": "other.txt"}
        }
    ]
    
    vs.add_chunks(chunks)
    assert vs.index.ntotal == 3
    print("Success: Chunks added to index.")

    # 2. Test search basic
    query = [1.0, 0.1, 0.0, 0.0]
    results = vs.search(query, top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "1"
    print(f"Success: Basic search returned correct top result (id: {results[0]['id']})")

    # 3. Test filter by document_id
    results_filtered = vs.search(query, top_k=5, document_id="doc2")
    assert len(results_filtered) == 1
    assert results_filtered[0]["id"] == "3"
    print("Success: Document filtering works.")

    # 4. Test Persistence
    vs.save()
    assert os.path.exists("test_faiss.bin")
    assert os.path.exists("test_metadata.json")
    print("Success: Files saved to disk.")

    # 5. Test Load
    vs2 = VectorStore(index_path="test_faiss.bin", metadata_path="test_metadata.json", dimension=4)
    assert vs2.index.ntotal == 3
    assert len(vs2.chunks) == 3
    print("Success: Data reloaded from disk.")

    # Cleanup
    os.remove("test_faiss.bin")
    os.remove("test_metadata.json")
    print("--- VectorStore Unit Test Passed! ---")

if __name__ == "__main__":
    try:
        test_vector_store()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

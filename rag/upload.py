import os
import time
import logging
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from datetime import datetime
from .parser import extract_text_from_file
from .chunker import chunk_text
from .embed import generate_embeddings
from .vector_store import vector_store

# Configure logger
logger = logging.getLogger(__name__)

# Constants
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create router
router = APIRouter(prefix="/api", tags=["Document Upload"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Endpoint for uploading PDF and TXT files.
    - Path: POST /api/upload
    - File size limit: 5MB
    - Supported formats: PDF, TXT
    - Returns: document_id, extracted text, and chunks (without embeddings)
    """
    document_id = str(uuid.uuid4())
    logger.info(f"Received upload request [{document_id}] for file: {file.filename} ({file.content_type})")

    # Validate file type
    if file.content_type not in ["application/pdf", "text/plain"]:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Only PDF and TXT files are accepted."
        )

    # Read content to check size and save
    try:
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes (Limit: {MAX_FILE_SIZE})")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds size limit of 5MB. (Current: {round(file_size / (1024 * 1024), 2)}MB)"
            )
        
        if file_size == 0:
            logger.warning(f"Empty file uploaded: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty files cannot be processed."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during file validation."
        )

    # Prepare file storage path
    original_filename = file.filename
    file_ext = os.path.splitext(original_filename)[1]
    saved_filename = f"{document_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"File saved to: {file_path}")

        # 1. Extract text
        extracted_text = extract_text_from_file(file_path, file.content_type)
        
        # 2. Chunk text
        chunks = chunk_text(extracted_text, original_filename, document_id)
        logger.info(f"Generated {len(chunks)} chunks for document {document_id}")

        # 3. Generate embeddings (Internal use)
        if chunks:
            chunk_texts = [c["text"] for c in chunks]
            try:
                embeddings = await generate_embeddings(chunk_texts)
                # Store embeddings in chunks internally (for future DB use)
                for i, chunk in enumerate(chunks):
                    chunk["embedding"] = embeddings[i]
                
                # Add to FAISS vector store and persist
                vector_store.add_chunks(chunks)
                logger.info(f"Successfully added {len(chunks)} chunks to vector store.")
                
            except Exception as embed_error:
                logger.error(f"Embedding generation failed: {embed_error}")
                # We continue even if embedding fails, or handle as needed
        
        # 4. Prepare response (Exclude embeddings as requested)
        response_chunks = []
        for chunk in chunks:
            response_chunks.append({
                "id": chunk["id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"]
            })

        return {
            "success": True,
            "document_id": document_id,
            "filename": original_filename,
            "saved_as": saved_filename,
            "length": len(extracted_text),
            "chunks_count": len(response_chunks),
            "chunks": response_chunks,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process upload for {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
    finally:
        await file.close()

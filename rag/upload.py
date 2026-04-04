import os
import time
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from datetime import datetime
from .parser import extract_text_from_file

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
    """
    logger.info(f"Received upload request for file: {file.filename} ({file.content_type})")

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
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Check if filename exists, append timestamp if so to avoid collision
    if os.path.exists(file_path):
        name, ext = os.path.splitext(file.filename)
        file_path = os.path.join(UPLOAD_DIR, f"{name}_{int(time.time())}{ext}")

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"File saved to: {file_path}")

        # Extract text
        extracted_text = extract_text_from_file(file_path, file.content_type)
        
        # Prepare response
        return {
            "success": True,
            "filename": os.path.basename(file_path),
            "text": extracted_text,
            "length": len(extracted_text),
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

import os
import re
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    Cleans extracted text by:
    1. Normalizing line breaks
    2. Removing excessive whitespace
    3. Trimming the result
    """
    if not text:
        return ""
    
    # Normalize line breaks to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Replace multiple spaces with a single space
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Replace multiple newlines (3+) with double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def extract_text_from_file(file_path: str, content_type: str) -> str:
    """
    Extracts and cleans text from PDF or TXT files.
    """
    text = ""
    try:
        if content_type == "application/pdf":
            logger.info(f"Extracting text from PDF: {file_path}")
            reader = PdfReader(file_path)
            all_page_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    all_page_text.append(page_text)
            text = "\n".join(all_page_text)
            
        elif content_type == "text/plain":
            logger.info(f"Reading text from TXT: {file_path}")
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            logger.warning(f"Unsupported content type for extraction: {content_type}")
            return ""

        cleaned_text = clean_text(text)
        logger.info(f"Successfully extracted {len(cleaned_text)} characters from {file_path}")
        return cleaned_text

    except Exception as e:
        logger.error(f"Error during text extraction from {file_path}: {str(e)}")
        raise e

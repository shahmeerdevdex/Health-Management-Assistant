from fastapi import UploadFile
import os
import shutil
from datetime import datetime
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def store_document(file: UploadFile) -> str:
    """
    Store an uploaded document and return its URL.
    In a production environment, this would use a proper cloud storage service.
    """
    try:
        # Generate a unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return the relative URL
        return f"/uploads/{filename}"
    except Exception as e:
        logger.error(f"Error storing document: {str(e)}")
        raise

async def get_document_url(file_path: str) -> Optional[str]:
    """
    Get the URL for a stored document.
    In a production environment, this would generate a signed URL for cloud storage.
    """
    try:
        if os.path.exists(os.path.join(UPLOAD_DIR, file_path)):
            return f"/uploads/{file_path}"
        return None
    except Exception as e:
        logger.error(f"Error getting document URL: {str(e)}")
        return None 
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Dict, Any
import uuid
import os
import tempfile
from datetime import datetime

from auth import get_current_user
from supabase_client import supabase_admin_client
from config import settings

router = APIRouter()

@router.post("/upload/persona-photo", response_model=Dict[str, str])
async def upload_persona_photo(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload a persona photo to Supabase storage.
    """
    user_id = current_user["user_id"]
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Limit file size (5MB)
    file_size_limit = 5 * 1024 * 1024  # 5MB
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > file_size_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit"
        )
    
    try:
        # Create a temporary file to store the uploaded file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Read the uploaded file and write to the temp file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{user_id}_{timestamp}_{file.filename}"
        
        # Upload the file to Supabase Storage
        with open(temp_file_path, 'rb') as f:
            result = supabase_admin_client.storage.from_('personas').upload(
                path=filename,
                file=f,
                file_options={
                    'content-type': file.content_type
                }
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Get the public URL for the uploaded file
        file_url = supabase_admin_client.storage.from_('personas').get_public_url(filename)
        
        return {"file_url": file_url}
    
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during file upload: {str(e)}"
        ) 
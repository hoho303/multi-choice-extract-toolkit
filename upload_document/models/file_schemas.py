from .base import BaseSchema
from pydantic import Field
from datetime import datetime
from typing import List

class FileUploadResponse(BaseSchema):
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    stored_filename: str = Field(..., description="Stored filename of the uploaded file")
    content_type: str = Field(..., description="Content type of the uploaded file")
    size: int = Field(..., description="Size of the uploaded file")
    upload_time: datetime = Field(..., description="Upload time of the uploaded file")
    location: str = Field(..., description="Location of the uploaded file")

class FileUploadErrorResponse(BaseSchema):
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    error_messages: List[str] = Field(..., description="Error messages of the uploaded file")

class MultipleFileUploadResponse(BaseSchema):
    total_files: int = Field(..., description="Total number of uploaded files")
    successsful: int = Field(..., description="Number of successful uploaded files")
    failed: int = Field(..., description="Number of failed uploaded files")
    successful_files: List[FileUploadResponse] = Field(..., description="List of successful uploaded files")
    failed_files: List[FileUploadErrorResponse] = Field(..., description="List of failed uploaded files")
from .base import BaseSchema
from pydantic import Field
from datetime import datetime
from typing import List

class CollectionCreateRequest(BaseSchema):
    name: str = Field(..., min_length=3, max_length=255)
    processing_status: str = Field(default='PENDING', min_length=3, max_length=255)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

class CollectionResponse(BaseSchema):
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=3, max_length=255)
    user_id: int = Field(..., ge=1)
    processing_status: str = Field(default='PENDING', min_length=3, max_length=255)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
from .base import BaseSchema
from pydantic import Field
from datetime import datetime
from typing import List

class FileCreateRequest(BaseSchema):
    collection_id: int = Field(..., ge=1)
    url: str = Field(..., min_length=3, max_length=255)
    file_order: int = Field(..., ge=1)
    created_at: datetime = Field(default=datetime.now())

class FileOrderUpdateRequest(BaseSchema):
    file_id: int = Field(..., ge=1)
    new_file_order: int = Field(..., ge=1)

class FileOrdersUpdateRequest(BaseSchema):
    file_orders: List[FileOrderUpdateRequest] = Field(..., min_length=1)

class FileResponse(BaseSchema):
    id: int = Field(..., ge=1)
    collection_id: int = Field(..., ge=1)
    url: str = Field(..., min_length=3, max_length=255)
    file_order: int = Field(..., ge=1)
    created_at: datetime = Field(default=datetime.now())

from pydantic import BaseModel, Field
from typing import List

class ExecuteCollectionsRequest(BaseModel):
    """Schema for batch execute collections"""
    collection_ids: List[int] = Field(..., description="Danh sách ID của collections")
from app.models.base import BaseSchema
from pydantic import Field

class ProgressMessage(BaseSchema):
    task_id: str = Field(..., description="The ID of the task")
    step: str = Field(..., description="The step of the task")
    percent: float = Field(..., description="The percent of the task")
    status: str = Field(..., description="The status of the task")
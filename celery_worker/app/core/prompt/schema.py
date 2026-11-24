from typing import Optional

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    name: str = Field(..., description="The name of the prompt")
    template: str = Field(..., description="The template string of the prompt")
    variables: Optional[list[str]] = Field(
        default_factory=list, description="List of variable names used in the template"
    )

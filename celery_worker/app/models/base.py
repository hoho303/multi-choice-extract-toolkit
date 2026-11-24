from pydantic import BaseModel    
from enum import Enum
from pydantic import Field

class BaseSchema(BaseModel):
    def to_dict(self):
        return self.model_dump(exclude_none=True)

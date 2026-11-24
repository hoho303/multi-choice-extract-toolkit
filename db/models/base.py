from pydantic import BaseModel

class BaseSchema(BaseModel):
    def to_dict(self):
        return self.model_dump(exclude_none=True)
from .base import BaseSchema
from typing import List
from enum import Enum
from pydantic import Field

class QuestionTypeEnum(str, Enum):
    MULTIPLE_CHOICE = 'MULTIPLE_CHOICE'
    READING_COMPREHENSION = 'READING_COMPREHENSION'
    TRUE_FALSE = 'TRUE_FALSE'

class TrueFalseAnswerEnum(str, Enum):
    TRUE = 'ĐÚNG'
    FALSE = 'SAI'

class QuestionExtract(BaseSchema):
    code: str = Field(..., description="The ID of the question")
    type: QuestionTypeEnum = Field(default=QuestionTypeEnum.MULTIPLE_CHOICE, description="The type of the question")
    content: str = Field(..., description="The content of the question")
    reference: str = Field(default="", description="The reference text or passage. Must be an empty string \"\" if not applicable")
    options: dict[str, str] = Field(default={})
    correct_answer: TrueFalseAnswerEnum | str | None = Field(default=None)

class QAExtract(BaseSchema):
    file_order: int
    questions: List[QuestionExtract]

class QAExtractResponse(BaseSchema):
    results: List[QAExtract]
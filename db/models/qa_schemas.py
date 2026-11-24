from .base import BaseSchema
from pydantic import Field
from typing import List
from enum import Enum
from datetime import datetime

class QuestionTypeEnum(str, Enum):
    MULTIPLE_CHOICE = 'MULTIPLE_CHOICE'
    READING_COMPREHENSION = 'READING_COMPREHENSION'
    TRUE_FALSE = 'TRUE_FALSE'

class TrueFalseAnswerEnum(str, Enum):
    TRUE = 'ĐÚNG'
    FALSE = 'SAI'

class QuestionCreateRequest(BaseSchema):
    file_id: int = Field(..., ge=1)
    html_content: str = Field(..., min_length=3)
    type: QuestionTypeEnum = Field(default=QuestionTypeEnum.MULTIPLE_CHOICE)
    reference: str = Field(default="", description="The reference text or passage. Must be an empty string \"\" if not applicable")
    code: str = Field(..., description="The ID of the question")
    created_at: datetime = Field(default=datetime.now())
    page_number: int = Field(..., ge=1)
    position_in_page: int = Field(..., ge=1)

class AnswerCreateRequest(BaseSchema):
    question_id: int = Field(default=None, ge=1)
    html_content: str = Field(..., min_length=3)
    is_correct: bool = Field(default=False)
    label: str = Field(..., min_length=1)
    created_at: datetime = Field(default=datetime.now())

class QACreateRequest(BaseSchema):
    question: QuestionCreateRequest = Field(..., description="The question to create")
    answers: List[AnswerCreateRequest] = Field(..., description="The list of answers")

class AnswerResponse(BaseSchema):
    id: int = Field(..., ge=1)
    html_content: str = Field(..., min_length=3)
    is_correct: bool = Field(default=False)
    label: str = Field(..., min_length=1)
    created_at: datetime = Field(default=datetime.now())

class QAResponse(BaseSchema):
    id: int = Field(..., ge=1)
    source_file_id: int = Field(..., ge=1)
    type: QuestionTypeEnum = Field(default=QuestionTypeEnum.MULTIPLE_CHOICE)
    html_content: str = Field(..., min_length=3)
    reference: str = Field(default="", description="The reference text or passage. Must be an empty string \"\" if not applicable")
    code: str = Field(..., description="The ID of the question")
    created_at: datetime = Field(default=datetime.now())
    page_number: int = Field(..., ge=1)
    position_in_page: int = Field(..., ge=1)
    answers: List[AnswerResponse] = Field(..., description="The list of answers")
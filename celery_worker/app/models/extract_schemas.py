from app.models.base import BaseSchema
from typing import List, Dict
from enum import Enum
from pydantic import Field, ConfigDict
from db.models.qa_schemas import QuestionTypeEnum, TrueFalseAnswerEnum
from db.common.models.file import File
from datetime import datetime

class ProgressStepPercentEnum(float, Enum):
    PREPROCESSING = 10
    EXTRACTING = 20
    POSTPROCESSING = 80
    COMPLETED = 100
    CRAWLING = 20

class QuestionExtract(BaseSchema):
    code: str = Field(..., description="The ID of the question")
    type: QuestionTypeEnum = Field(default=QuestionTypeEnum.MULTIPLE_CHOICE, description="The type of the question")
    content: str = Field(..., description="The content of the question")
    reference: str = Field(default="", description="The reference text or passage. Must be an empty string \"\" if not applicable")
    options: dict[str, str] = Field(default=None)
    correct_answer: TrueFalseAnswerEnum | str | None = Field(default=None)
    page_number: int = Field(..., description="The page number of the question")
    position_in_page: int = Field(..., description="The position of the question in the page")

# class QAExtract(BaseSchema):
#     file_order: int
#     questions: List[QuestionExtract]

class QAExtractLLMResponse(BaseSchema):
    # results: List[QAExtract]
    results: Dict[int, List[QuestionExtract]]

class FileSchema(BaseSchema):
    id: int
    collection_id: int
    url: str
    file_order: int
    created_at: datetime
    is_deleted: bool = False

class FileExtractLLMResponse(BaseSchema):
    file: FileSchema
    total_pages: int
    results: List[QuestionExtract]

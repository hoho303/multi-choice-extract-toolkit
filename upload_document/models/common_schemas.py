from .base import BaseSchema
from typing import Any

class BaseResponse(BaseSchema):
    message: str
    status_code: int
    data: Any = None

class ApiSuccessResponse(BaseResponse):
    message: str = "Success"
    status_code: int = 200
    data: Any = None

class ApiErrorResponse(BaseResponse):
    message: str = "Error"
    status_code: int = 500
    data: Any = None

class ApiValidationErrorResponse(BaseResponse):
    message: str = "Validation Error"
    status_code: int = 400
    data: Any = None

class ApiNotFoundErrorResponse(BaseResponse):
    message: str = "Not Found"
    status_code: int = 404
    data: Any = None

class ApiBadRequestErrorResponse(BaseResponse):
    message: str = "Bad Request"
    status_code: int = 400
    data: Any = None
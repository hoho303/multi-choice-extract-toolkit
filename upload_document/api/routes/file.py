from fastapi import APIRouter, Depends
from typing import Dict
from core import cfg
from sqlalchemy.orm import Session
from models.common_schemas import BaseResponse, ApiErrorResponse, ApiSuccessResponse
from services.upload_service.validator import DocumentValidator
from fastapi import UploadFile, File
from pathlib import Path
import uuid
import shutil
from datetime import datetime
from models.file_schemas import FileUploadResponse, FileUploadErrorResponse, MultipleFileUploadResponse
import asyncio
from typing import List
from fastapi.staticfiles import StaticFiles

router = APIRouter()

document_validator = DocumentValidator(max_size=100 * 1024 * 1024)

@router.post("/upload/single")
async def upload_file(file: UploadFile = File(...)):
    validation_result = await document_validator.validate_file(file)

    if not validation_result["valid"]:
        return ApiErrorResponse(message="Validation error", errors=validation_result["errors"])

    # Create unique filename to prevent conflicts
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = Path(cfg.settings.UPLOAD_DIR) / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return ApiErrorResponse(message=f"Error uploading file: {str(e)}", status_code=500)

    response = FileUploadResponse(
        original_filename=file.filename,
        stored_filename=unique_filename,
        content_type=file.content_type,
        size=file.size,
        upload_time=datetime.now(),
        location=str(file_path)
    )
    return ApiSuccessResponse(message="File uploaded successfully", data=response.to_dict())

@router.post("/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    validation_results = await asyncio.gather(*[document_validator.validate_file(file) for file in files])
    successful_files = []
    failed_files = []

    for file, validation_result in zip(files, validation_results):

        if not validation_result["valid"]:
            failed_files.append(FileUploadErrorResponse(
                original_filename=file.filename,
                error_messages=validation_result["errors"]
            ))
            continue

        # Create unique filename to prevent conflicts
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = Path(cfg.settings.UPLOAD_DIR) / unique_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            failed_files.append(FileUploadErrorResponse(
                original_filename=file.filename,
                error_messages=[f"Error uploading file: {str(e)}"]
            ))
            continue

        successful_files.append(FileUploadResponse(
            original_filename=file.filename,
            stored_filename=unique_filename,
            content_type=file.content_type,
            size=file.size,
            upload_time=datetime.now(),
            location=str(file_path)
        ))

    response = MultipleFileUploadResponse(
        total_files=len(files),
        successsful=len(successful_files),
        failed=len(failed_files),
        successful_files=successful_files,
        failed_files=failed_files)

    return ApiSuccessResponse(message="Files uploaded successfully", data=response.to_dict())
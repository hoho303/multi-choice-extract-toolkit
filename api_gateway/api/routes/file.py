from fastapi import APIRouter, Depends
from typing import Dict
from db.models.file_schemas import FileCreateRequest
from models.common_schemas import BaseResponse, ApiErrorResponse, ApiSuccessResponse
from db.services.file_service import create_file_to_db, get_file_by_id, delete_file_by_id, get_files_by_collection_id
from core import cfg
from sqlalchemy.orm import Session
from api.routes.auth import get_current_user
from models.common_schemas import APIException

router = APIRouter()

@router.post("/create", response_model=BaseResponse)
async def create_file(
    file: FileCreateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Tạo file - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = create_file_to_db(db, file)

        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)

        return response

@router.get("/get/{file_id}", response_model=BaseResponse)
async def get_file(
    file_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Lấy file - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = get_file_by_id(db, file_id)
        file = response.data

        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
            
        return ApiSuccessResponse(message="Đã lấy file thành công", data=file.to_dict())

@router.get("/get-all/{collection_id}", response_model=BaseResponse)
async def get_all_files_by_collection_id(
    collection_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Lấy tất cả files - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        try:
            response = get_files_by_collection_id(db, collection_id)
            files = response.data
            files_dict = [file.to_dict() for file in files]
            
            if response.status_code != 200:
                raise APIException(status_code=response.status_code, response=response)
                
            return ApiSuccessResponse(message="Đã lấy tất cả files thành công", data=files_dict)
            
        except Exception as e:
            raise APIException(status_code=500, response=ApiErrorResponse(message=str(e), status_code=500, data=[]))

@router.delete("/delete/{file_id}", response_model=BaseResponse)
async def delete_file(
    file_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Xóa file - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = delete_file_by_id(db, file_id)
        
        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return response
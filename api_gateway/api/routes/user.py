from fastapi import APIRouter, Depends
from typing import Dict
from models.common_schemas import BaseResponse, ApiErrorResponse, ApiSuccessResponse
from db.services.user_service import get_all_users_db
from core import cfg
from sqlalchemy.orm import Session
from api.routes.auth import get_current_user
from models.common_schemas import APIException

router = APIRouter()

@router.get("/get-all", response_model=BaseResponse)
async def get_all_users():
    with Session(cfg.postgres_client.get_engine()) as db:
        response = get_all_users_db(db)
        
        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return response
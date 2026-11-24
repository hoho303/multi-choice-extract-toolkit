from db.common.models.user import User
from db.models.user_schemas import UserRegisterRequest, UserLoginRequest, UserResponse, TokenVerifyRequest, TokenRefreshRequest
from db.utils import Hasher
from sqlalchemy.orm import Session
from db.models.common_schemas import (
    ApiSuccessResponse, 
    ApiErrorResponse, 
    ApiValidationErrorResponse, 
    ApiNotFoundErrorResponse, 
    ApiBadRequestErrorResponse
)

def create_user(db: Session, user: UserRegisterRequest):
    try:
        user = User(
            username=user.username,
            email=user.email,
            hashed_password=Hasher.hash_password(user.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return ApiSuccessResponse(data=user.to_dict())
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return ApiNotFoundErrorResponse(message="Không tìm thấy User")
    return ApiSuccessResponse(data=user)

def get_all_users_db(db: Session):
    users = db.query(User).all()
    if not users:
        return ApiNotFoundErrorResponse(message="Không tìm thấy Users")
    return ApiSuccessResponse(data=[user.to_dict() for user in users])
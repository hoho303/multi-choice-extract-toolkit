from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import jwt
import hashlib
from functools import wraps

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from db.models.user_schemas import (
    UserRegisterRequest, 
    UserLoginRequest, 
    TokenResponse, 
    TokenVerifyRequest, 
    TokenRefreshRequest
)
from models.common_schemas import BaseResponse, ApiErrorResponse, ApiSuccessResponse
from db.services.user_service import create_user, get_user_by_username
from core import cfg
from sqlalchemy.orm import Session
from db.utils import Hasher
from fastapi import HTTPException
from models.common_schemas import APIException

# Cấu hình
SECRET_KEY = "your-secret-key-change-this-in-production"  # TODO: Di chuyển vào .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Router
router = APIRouter()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Tạo JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """Giải mã JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token(token: str) -> Dict:
    """Xác minh token là access token"""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không phải là access token",
        )
    return payload

# Endpoints
@router.post("/register", response_model=BaseResponse)
async def register(user_data: UserRegisterRequest):
    with Session(cfg.postgres_client.get_engine()) as db:
        response = create_user(db, user_data)

        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)

        return response

@router.post("/login", response_model=BaseResponse)
async def login(credentials: UserLoginRequest):
    """
    Đăng nhập và nhận JWT tokens
    
    - **username**: Tên người dùng
    - **password**: Mật khẩu
    
    Returns:
    - **access_token**: Token để truy cập API (hết hạn sau 30 phút)
    - **refresh_token**: Token để cấp lại access token (hết hạn sau 7 ngày)
    - **token_type**: Loại token (bearer)
    - **expires_in**: Thời gian hết hạn của access token (giây)
    """
    # Tìm user
    with Session(cfg.postgres_client.get_engine()) as db:
        response = get_user_by_username(db, credentials.username)
        user = response.data

    if not user or not Hasher.verify_password(credentials.password, user.hashed_password):
        raise APIException(status_code=401, response=ApiErrorResponse(
            message="Tên người dùng hoặc mật khẩu không chính xác",
            status_code=401,
        ))
    
    # Tạo tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_data = {"sub": credentials.username, "user_id": user.id}
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data=token_data)
    
    return ApiSuccessResponse(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    ))

@router.post("/verify-token", response_model=BaseResponse)
async def verify_token_endpoint(token_data: TokenVerifyRequest):
    """
    Xác minh JWT token
    
    - **token**: JWT token cần xác minh
    
    Returns:
    - Thông tin user được encode trong token nếu hợp lệ
    - Lỗi 401 nếu token hết hạn hoặc không hợp lệ
    """
    payload = verify_token(token_data.token)
    return ApiSuccessResponse(data={
        "valid": True,
        "username": payload.get("sub"),
        "user_id": payload.get("user_id"),
        "expires_at": datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
    })

@router.post("/refresh", response_model=BaseResponse)
async def refresh_access_token(token_data: TokenRefreshRequest):
    """
    Làm mới access token bằng refresh token
    
    - **refresh_token**: Refresh token
    
    Returns:
    - Access token mới
    - Refresh token mới (tùy chọn)
    """
    try:
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise APIException(status_code=401, response=ApiErrorResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Token không phải là refresh token",
            ))
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not username:
            raise APIException(status_code=401, response=ApiErrorResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Refresh token không hợp lệ",
            ))
        
        # Tạo access token mới
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data_new = {"sub": username, "user_id": user_id}
        
        new_access_token = create_access_token(
            data=token_data_new,
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(data=token_data_new)
        
        return ApiSuccessResponse(data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ).to_dict())
        
    except jwt.ExpiredSignatureError:
        raise APIException(status_code=401, response=ApiErrorResponse(
            message="Refresh token đã hết hạn",
            status_code=401,
        ))
    except jwt.InvalidTokenError:
        raise APIException(status_code=401, response=ApiErrorResponse(
            message="Refresh token không hợp lệ",
            status_code=401,
        ))

@router.post("/logout")
async def logout():
    """
    Đăng xuất (client-side, xóa token)
    
    Lưu ý: JWT là stateless nên logout chỉ được thực hiện phía client
    bằng cách xóa token. Nếu cần logout phía server, hãy sử dụng 
    token blacklist/revocation.
    """
    return {
        "message": "Đã đăng xuất thành công",
        "detail": "Vui lòng xóa token từ client"
    }

# Dependency để xác minh token
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """
    Dependency để xác minh token trong các endpoint khác
    
    Sử dụng:
    @app.get("/protected")
    async def protected_route(current_user: Dict = Depends(get_current_user)):
        return {"message": f"Hello {current_user['sub']}"}
    
    Headers:
    - Authorization: Bearer <token>
    """
    if not authorization:
        raise APIException(status_code=401, response=ApiErrorResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Authorization header bị thiếu",
            headers={"WWW-Authenticate": "Bearer"},
        ))
    
    # Tách token từ header "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise APIException(status_code=401, response=ApiErrorResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Authorization header không hợp lệ. Format: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            ))
    except ValueError:
        raise APIException(status_code=401, response=ApiErrorResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Authorization header không hợp lệ. Format: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        ))
    
    return verify_token(token)


from fastapi import APIRouter, WebSocket, Depends, Query, status, Header
from typing import Dict

from db.models.collection_schemas import CollectionCreateRequest
from db.models.file_schemas import FileOrdersUpdateRequest
from models.common_schemas import BaseResponse, ApiErrorResponse, ApiSuccessResponse
from db.services.collection_service import create_collection_to_db, get_collection_by_id, get_all_collections_by_user_id
from db.services.qa_service import create_qa_to_db, get_qa_by_collection_id
from core import cfg
from sqlalchemy.orm import Session
from db.services.file_service import get_files_by_collection_id, update_file_orders_by_collection_id
from celery.result import AsyncResult
from api.routes.auth import get_current_user
from db.common.models.collection import ProcessingStatusEnum
from db.services.collection_service import update_status_collection, delete_collection_from_db
from models.collection_schemas import ExecuteCollectionsRequest
from models.common_schemas import APIException

router = APIRouter()

@router.post("/create", response_model=BaseResponse)
async def create_collection(
    collection: CollectionCreateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Tạo collection - Cần xác thực"""
    user_id = current_user.get('user_id')
    with Session(cfg.postgres_client.get_engine()) as db:
        response = create_collection_to_db(db, user_id, collection)

        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return response

@router.get("/get-all", response_model=BaseResponse)
async def get_all_collections(
    current_user: Dict = Depends(get_current_user)
):
    """Lấy tất cả collection của user - Cần xác thực"""
    user_id = current_user['user_id']
    with Session(cfg.postgres_client.get_engine()) as db:
        response = get_all_collections_by_user_id(db, user_id)
        
        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return response

@router.get("/get/{collection_id}", response_model=BaseResponse)
async def get_collection(
    collection_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Lấy chi tiết collection - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = get_collection_by_id(db, collection_id)
        collection = response.data

        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return ApiSuccessResponse(message="Đã lấy collection thành công", data=collection.to_dict())

@router.get("/get-qa/{collection_id}", response_model=BaseResponse)
async def get_qa_by_collection(
    collection_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Lấy QA từ collection - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = get_qa_by_collection_id(db, collection_id)
        qa_list = response.data

        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
            
        return ApiSuccessResponse(message="Đã lấy danh sách QA thành công", data=qa_list)

@router.post("/execute/{collection_id}", response_model=BaseResponse)
async def execute_collection(
    collection_id: int,
    current_user: Dict = Depends(get_current_user),
    authorization: str = Header(...)
):
    """Thực thi collection - Cần xác thực"""
    session_id = authorization.split()[1]
    print(f"Session ID: {session_id}")
    if not session_id:
        raise APIException(status_code=400, response=ApiErrorResponse(message="Session ID không tồn tại", status_code=400))
    
    with Session(cfg.postgres_client.get_engine()) as db:
        # Update status collection to PROCESSING
        update_status_collection(db, collection_id, ProcessingStatusEnum.PROCESSING)
        
        response = get_files_by_collection_id(db, collection_id)
        files = response.data
    
    if response.status_code != 200:
        raise APIException(status_code=response.status_code, response=response)

    files_dict = [file.to_dict() for file in files]
    result = cfg.celery_app.send_task("extract_qa_task", args=[session_id, collection_id, files_dict])
    
    return ApiSuccessResponse(message="Đã thực thi collection thành công", data=result.id)

@router.post("/execute-batch", response_model=BaseResponse)
async def execute_batch_collections(
    request: ExecuteCollectionsRequest,
    current_user: Dict = Depends(get_current_user),
    authorization: str = Header(...)
):
    """Thực thi mảng collections - Cần xác thực"""
    session_id = authorization.split()[1]
    print(f"Session ID: {session_id}")
    if not session_id:
        raise APIException(status_code=400, response=ApiErrorResponse(message="Session ID không tồn tại", status_code=400))
    
    if not request.collection_ids or len(request.collection_ids) == 0:
        raise APIException(status_code=400, response=ApiErrorResponse(message="Danh sách collection_ids không được rỗng", status_code=400))
    
    task_ids = []
    errors = []
    
    with Session(cfg.postgres_client.get_engine()) as db:
        for collection_id in request.collection_ids:
            try:
                # Update status collection to PROCESSING
                update_status_collection(db, collection_id, ProcessingStatusEnum.PROCESSING)
                
                response = get_files_by_collection_id(db, collection_id)
                files = response.data
                
                if response.status_code != 200:
                    errors.append({
                        "collection_id": collection_id,
                        "error": response.message
                    })
                    continue
                
                files_dict = [file.to_dict() for file in files]
                result = cfg.celery_app.send_task("extract_qa_task", args=[session_id, collection_id, files_dict])
                task_ids.append({
                    "collection_id": collection_id,
                    "task_id": result.id
                })
            except Exception as e:
                errors.append({
                    "collection_id": collection_id,
                    "error": str(e)
                })
    
    response_data = {
        "task_ids": task_ids,
        "errors": errors if errors else None
    }
    
    if errors and len(task_ids) == 0:
        raise APIException(status_code=400, response=ApiErrorResponse(
            message=f"Thất bại: Tất cả {len(request.collection_ids)} collections đều có lỗi",
            status_code=400
        ))
    
    message = f"Đã thực thi thành công {len(task_ids)}/{len(request.collection_ids)} collections"
    return ApiSuccessResponse(message=message, data=response_data)

@router.get("/import-files-from-web/{collection_id}", response_model=BaseResponse)
async def import_files_from_web(
    collection_id: int,
    url: str = Query(...),
    current_user: Dict = Depends(get_current_user),
    authorization: str = Header(...)
):
    """Thực thi collection - Cần xác thực"""
    session_id = authorization.split()[1]
    print(f"Session ID: {session_id}")
    if not session_id:
        raise APIException(status_code=400, response=ApiErrorResponse(message="Session ID không tồn tại", status_code=400))
    
    result = cfg.celery_app.send_task("import_files_from_web_task", args=[session_id, collection_id, url])
    
    return ApiSuccessResponse(message="Đã thêm task nhập files từ web thành công", data=result.id)

@router.put("/update-file-orders/{collection_id}", response_model=BaseResponse)
async def update_file_orders(
    collection_id: int,
    file_orders: FileOrdersUpdateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Cập nhật thứ tự files trong collection - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = update_file_orders_by_collection_id(db, collection_id, file_orders)
        
        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return response

@router.get("/get-result/{task_id}", response_model=BaseResponse)
async def get_result(
    task_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Lấy kết quả task - Cần xác thực"""
    result = AsyncResult(task_id, app=cfg.celery_app)
    if result:
        if result.status == "PENDING":
            return ApiSuccessResponse(message="Đang xử lý", data=result.id)
        elif result.status == "SUCCESS":
            if result.result:
                return ApiSuccessResponse(message="Đã xử lý thành công", data=result.result)
            else:
                raise APIException(status_code=500, response=ApiErrorResponse(message="Đã xử lý thất bại", status_code=500))
        else:
            raise APIException(status_code=500, response=ApiErrorResponse(message="Đã xử lý thất bại", status_code=500))
    else:
        raise APIException(status_code=404, response=ApiErrorResponse(message="Task không tồn tại hoặc đã xảy ra lỗi", status_code=404))

@router.delete("/delete/{collection_id}", response_model=BaseResponse)
async def delete_collection(
    collection_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Xóa collection - Cần xác thực"""
    with Session(cfg.postgres_client.get_engine()) as db:
        response = delete_collection_from_db(db, collection_id)
        
        if response.status_code != 200:
            raise APIException(status_code=response.status_code, response=response)
        
        return response

@router.websocket("/ws/progress/{session_id}/{collection_id}")
async def progress_websocket(
    websocket: WebSocket,
    session_id: str,
    collection_id: int
):
    """
    WebSocket để theo dõi tiến độ collection - Cần xác thực
    
    URL: ws://localhost:3333/api/collection/ws/progress/{collection_id}?session_id=<session_id>
    """
    await websocket.accept()
    print(f"WebSocket accepted for session_id: {session_id} and collection_id: {collection_id}")
    pubsub = cfg.redis_client.pubsub()
    
    # channel_name = f"extract_qa_task_{session_id}_{collection_id}"
    channel_name = f"extract_qa_task_{session_id}_{collection_id}"
    print(f"Subscribing to channel: {channel_name}")
    
    await pubsub.subscribe(channel_name)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                await websocket.send_text(message['data'].decode()) # Gửi thẳng payload xuống client
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await websocket.close()
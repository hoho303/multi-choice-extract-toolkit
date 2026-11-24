from db.common.models.file import File
from db.models.file_schemas import FileCreateRequest, FileResponse
from sqlalchemy.orm import Session
from db.models.common_schemas import ApiSuccessResponse, ApiErrorResponse, ApiNotFoundErrorResponse
from db.models.file_schemas import FileOrdersUpdateRequest

def create_file_to_db(db: Session, file: FileCreateRequest):
    try:
        db_file = File(collection_id=file.collection_id, url=file.url, file_order=file.file_order)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return ApiSuccessResponse(data=db_file.to_dict())
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def get_file_by_id(db: Session, file_id: int):
    db_file = db.query(File).filter(File.id == file_id).first()
    if not db_file:
        return ApiNotFoundErrorResponse(message="Không tìm thấy File")
    return ApiSuccessResponse(data=db_file)

def get_files_by_collection_id(db: Session, collection_id: int):
    db_files = db.query(File).filter(File.collection_id == collection_id, File.is_deleted == False).order_by(File.file_order).all()
    if not db_files:
        return ApiNotFoundErrorResponse(message="Không tìm thấy Files", data=[])
    return ApiSuccessResponse(data=db_files)

def update_file_orders_by_collection_id(db: Session, collection_id: int, file_orders: FileOrdersUpdateRequest):
    try:
        for file_order in file_orders.file_orders:
            db_file = db.query(File).filter(
                File.id == file_order.file_id,
                File.collection_id == collection_id,
                File.is_deleted == False
            ).first()
            
            if not db_file:
                return ApiNotFoundErrorResponse(message=f"Không tìm thấy File với id {file_order.file_id}")
            
            db_file.file_order = file_order.new_file_order
        
        db.commit()
        return ApiSuccessResponse(message="Cập nhật thứ tự file thành công")
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def delete_file_by_id(db: Session, file_id: int):
    db_file = db.query(File).filter(File.id == file_id).first()
    if not db_file:
        return ApiNotFoundErrorResponse(message="Không tìm thấy File")
    db_file.is_deleted = True
    db.commit()
    return ApiSuccessResponse(message="Đã xóa File thành công")
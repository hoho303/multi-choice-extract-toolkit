from db.common.models.collection import Collection
from db.models.collection_schemas import CollectionCreateRequest
from sqlalchemy.orm import Session
from db.models.common_schemas import ApiSuccessResponse, ApiErrorResponse, ApiNotFoundErrorResponse
from db.common.models.collection import ProcessingStatusEnum

def create_collection_to_db(db: Session, user_id: int, collection: CollectionCreateRequest):
    try:
        db_collection = Collection(name=collection.name, user_id=user_id, processing_status=collection.processing_status)
        db.add(db_collection)
        db.commit()
        db.refresh(db_collection)
        return ApiSuccessResponse(data=db_collection.to_dict())
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def get_collection_by_id(db: Session, collection_id: int):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.is_deleted == False).first()
    if not collection:
        return ApiNotFoundErrorResponse(message="Không tìm thấy Collection")
    return ApiSuccessResponse(data=collection)

def get_all_collections_by_user_id(db: Session, user_id: int):
    try:
        collections = db.query(Collection).filter(Collection.user_id == user_id, Collection.is_deleted == False).all()
        if not collections:
            return ApiNotFoundErrorResponse(message="Không tìm thấy Collections", data=[])
        return ApiSuccessResponse(data=[collection.to_dict() for collection in collections], message="Lấy danh sách Collections thành công")
    except Exception as e:
        return ApiErrorResponse(message=str(e), status_code=500, data=[])

def update_status_collection(db: Session, collection_id: int, status: ProcessingStatusEnum):
    try:
        db_collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not db_collection:
            return ApiNotFoundErrorResponse(message="Không tìm thấy Collection")
        db_collection.processing_status = ProcessingStatusEnum(status)
        db.commit()
        db.refresh(db_collection)
        return ApiSuccessResponse(data=db_collection.to_dict())
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def delete_collection_from_db(db: Session, collection_id: int):
    try:
        db_collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not db_collection:
            return ApiNotFoundErrorResponse(message="Không tìm thấy Collection")
        db_collection.is_deleted = True
        db.commit()
        db.refresh(db_collection)
        return ApiSuccessResponse(message="Collection deleted successfully")
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)
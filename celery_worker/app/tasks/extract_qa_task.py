import time
from loguru import logger
from sqlalchemy.orm import Session
from db.common.models.collection import ProcessingStatusEnum
from db.services.qa_service import create_qa_to_db, delete_qa_by_collection_id
from db.services.collection_service import update_status_collection
from app.services.extract_service import extract_qa_from_files, export_qa_create_requests
from app.services.redis_service import publish_progress_task_by_id
from app.models.message_schemas import ProgressMessage
from app.models.extract_schemas import ProgressStepPercentEnum
from app.core import cfg
from app.models.extract_schemas import FileSchema

def register_extract_qa_task(celery):
    """
    Register extract_qa_task to celery instance
    """
    @celery.task(name="extract_qa_task", bind=True)
    def extract_qa_task(self, session_id: str, collection_id: int, files: list[dict]):
        """
        Extract QA from files URL.
        """
        files = [FileSchema.model_validate(file) for file in files]
        task_id = self.request.id
        
        time.sleep(1)
        logger.info(f"Bắt đầu xử lý Collection {collection_id}... ")
        publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="PREPROCESSING", percent=ProgressStepPercentEnum.PREPROCESSING, status="Đang tiền xử lý"))
        
        with Session(cfg.postgres_client.get_engine()) as db:
            # Delete QA by collection id
            logger.info(f"Xóa Question và Answer cũ trong collection: {collection_id}")
            delete_qa_by_collection_id(db, collection_id)
            
            # result = extract_qa_from_images(gemini_model, files)
            publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="EXTRACTING", percent=ProgressStepPercentEnum.EXTRACTING, status="Đang trích xuất"))
            files_qa_extracts = extract_qa_from_files(cfg.gemini_model, files)
            
            if not files_qa_extracts:
                publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã xử lý thất bại"))
                update_status_collection(db, collection_id, ProcessingStatusEnum.FAILED)
                return None
            
            publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="POSTPROCESSING", percent=ProgressStepPercentEnum.POSTPROCESSING, status="Đang post-processing"))
            qa_create_requests = export_qa_create_requests(files_qa_extracts)

            for qa_create_request in qa_create_requests:
                response = create_qa_to_db(db, qa_create_request)
                
                if response.status_code != 200:
                    logger.error(f"Đã xử lý Collection {collection_id} thất bại: {response.message}")
                    update_status_collection(db, collection_id, ProcessingStatusEnum.FAILED)
                    
                    # Xóa QA nếu xử lý thất bại
                    logger.info(f"Bắt đầu quá trình rollback: {response.message}")
                    rollback_response = delete_qa_by_collection_id(db, collection_id)
                    
                    if rollback_response.status_code != 200:
                        logger.error(f"Rollback thất bại: {rollback_response.message}")
                        publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã xử lý thất bại"))
                        return None

                    logger.info(f"Rollback thành công")
                    publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã xử lý thất bại"))
                    
                    return None

            publish_progress_task_by_id("extract_qa_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã hoàn thành"))
            update_status_collection(db, collection_id, ProcessingStatusEnum.COMPLETED)
        return [file_qa_extract.to_dict() for file_qa_extract in files_qa_extracts]


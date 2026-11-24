from loguru import logger
from sqlalchemy.orm import Session
from db.models.file_schemas import FileCreateRequest
from db.services.file_service import create_file_to_db
from app.services.redis_service import publish_progress_task_by_id
from app.models.message_schemas import ProgressMessage
from app.models.extract_schemas import ProgressStepPercentEnum
from app.services.selenium_service import crawl_urls_with_selenium
from app.services.image_service import is_document_image_llm
from app.core import cfg


def register_import_files_from_web_task(celery):
    """
    Register import_files_from_web_task to celery instance
    """
    @celery.task(name="import_files_from_web_task", bind=True)
    def import_files_from_web_task(self, session_id: str, collection_id: int, url: str):
        """
        Crawl files from web.
        """
        task_id = self.request.id
        logger.info(f"Bắt đầu crawl files từ web {url}... ")
        publish_progress_task_by_id("import_files_from_web_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="CRAWLING", percent=ProgressStepPercentEnum.CRAWLING, status="Đang trích xuất"))
        
        with Session(cfg.postgres_client.get_engine()) as db:
            # Crawl files from web
            image_urls, pdf_urls = crawl_urls_with_selenium(url)

            logger.info(f"Có {len(image_urls)} ảnh được tìm thấy")
            logger.info(f"Kiểm tra xem ảnh có phải là ảnh đề thi không bằng LLM")

            for image_url in image_urls:
                is_document_image = is_document_image_llm(image_url, cfg.gemini_model)
                if not is_document_image:
                    logger.info(f"Ảnh {image_url} không phải là ảnh đề thi")
                    image_urls.remove(image_url)

            logger.info(f"Có {len(image_urls)} ảnh được tìm thấy là ảnh đề thi")
            
            file_urls = image_urls + pdf_urls

            if len(file_urls) == 0:
                publish_progress_task_by_id("import_files_from_web_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã xử lý thất bại"))
                return None

            publish_progress_task_by_id("import_files_from_web_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="POSTPROCESSING", percent=ProgressStepPercentEnum.POSTPROCESSING, status="Đang thêm file vào database"))
            
            for i, file_url in enumerate(file_urls):
                response = create_file_to_db(db, FileCreateRequest(collection_id=collection_id, url=file_url, file_order=i + 1))
                if response.status_code != 200:
                    logger.error(f"Đã xử lý Collection {collection_id} thất bại: {response.message}")
                    publish_progress_task_by_id("import_files_from_web_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã xử lý thất bại"))
                    return None
            publish_progress_task_by_id("import_files_from_web_task", collection_id, session_id, ProgressMessage(task_id=task_id, step="COMPLETED", percent=ProgressStepPercentEnum.COMPLETED, status="Đã hoàn thành"))
            return True


from app.core.prompt.prompt_manager import prompt_manager
from loguru import logger
import requests
from typing import List
from app.utils import convert_pdf_to_pil, convert_images_to_pdf
from app.utils import ImageProcessor
from app.models.extract_schemas import QAExtractLLMResponse, FileExtractLLMResponse
import os
import uuid
from app.core.cfg import settings
from db.models.qa_schemas import (
    QuestionCreateRequest, 
    AnswerCreateRequest, 
    QACreateRequest, 
    QuestionTypeEnum, 
    TrueFalseAnswerEnum
)
from app.models.extract_schemas import FileSchema

SUPPORTED_CONTENT_TYPES = ["PDF", "Image"]

class LocalFile(FileSchema):
    local_path: str

def _download_pdf_files(pdf_files: list[FileSchema], save_dir: str) -> List[LocalFile]:
    # Download tất cả các file PDF và lưu vào local
    local_files = []
    for pdf_file in pdf_files:
        pdf_url = pdf_file.url
        response = requests.get(pdf_url, allow_redirects=True, timeout=300)
        response.raise_for_status()
        pdf_bytes = response.content
        pdf_name = f"{uuid.uuid4()}.pdf"
        local_file = LocalFile(
            id=pdf_file.id,
            collection_id=pdf_file.collection_id,
            url=pdf_file.url,
            file_order=pdf_file.file_order,
            created_at=pdf_file.created_at,
            is_deleted=pdf_file.is_deleted,
            local_path=os.path.join(save_dir, pdf_name)
        )

        with open(os.path.join(save_dir, pdf_name), "wb") as f:
            f.write(pdf_bytes)
        local_files.append(local_file)

    return local_files

def _get_content_type(url: str) -> str:
    
    ### Kiểm tra dựa trên url
    if url.endswith(".pdf"):
        return SUPPORTED_CONTENT_TYPES[0]
    elif url.endswith(".jpg") or url.endswith(".jpeg") or url.endswith(".png") or url.endswith(".gif"):
        return SUPPORTED_CONTENT_TYPES[1]

    """Kiểm tra loại file dựa trên header Content-Type."""
    try:
        # Gửi yêu cầu HEAD để chỉ lấy header, không tải toàn bộ file
        # allow_redirects=True để xử lý các URL bị chuyển hướng
        # timeout=5 để tránh chờ quá lâu
        response = requests.head(url, allow_redirects=True, timeout=5)
        
        # Kiểm tra nếu yêu cầu thành công (status code 2xx)
        response.raise_for_status() 

        # Lấy header 'Content-Type', nếu không có thì trả về chuỗi rỗng
        content_type = response.headers.get('content-type', '').lower()

        if 'application/pdf' in content_type:
            return SUPPORTED_CONTENT_TYPES[0]
        elif 'image' in content_type:
            # Ví dụ: 'image/jpeg', 'image/png', 'image/gif'...
            return SUPPORTED_CONTENT_TYPES[1]
        else:
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting content type from URL: {e}")
        return None

def extract_qa_from_files(model, files: list[FileSchema]) -> List[FileExtractLLMResponse] | None:
    """
    Extract QA from PDF files.
    """
    try:
        image_files = []
        pdf_files = []

        # Kiểm tra và lấy tất cả các url của file PDF và ảnh
        for file in files:
            file_url = file.url
            content_type = _get_content_type(file_url)
            if content_type == "PDF":
                pdf_files.append(file)
            elif content_type == "Image":
                image_files.append(file)

        results: List[FileExtractLLMResponse] = []
        # ==================== Xử lý PDF ===========================
        # Download tất cả các file PDF và lưu vào local
        pdf_files = _download_pdf_files(pdf_files, settings.BASE_SAVE_DIR)
        user_prompt = prompt_manager.render("extract_qa_from_pdf_v2")

        for pdf_file in pdf_files:
            response = model.generate_pdf_content(user_prompt, pdf_file.local_path, QAExtractLLMResponse)
            response = QAExtractLLMResponse.model_validate_json(response.text)

            qa_extracts = response.results[1]
            total_pages = len(set(qa_extract.page_number for qa_extract in qa_extracts))
            results.append(FileExtractLLMResponse(
                            file=pdf_file, 
                            total_pages=total_pages, 
                            results=qa_extracts))
        

        # ==================== Xử lý ảnh ===========================
        # Convert tất cả các ảnh thành 1 file PDF và lưu vào local
        if len(image_files) > 0:
            img_pdf_name = f"{uuid.uuid4()}.pdf"
            image_urls = [image_file.url for image_file in image_files]
            convert_images_to_pdf(image_urls, os.path.join(settings.BASE_SAVE_DIR, img_pdf_name))

            img_pdf_path = os.path.join(settings.BASE_SAVE_DIR, img_pdf_name)
            response = model.generate_pdf_content(user_prompt, img_pdf_path, QAExtractLLMResponse)
            response = QAExtractLLMResponse.model_validate_json(response.text)
            
            qa_extracts = response.results[1]
            total_pages = len(set(qa_extract.page_number for qa_extract in qa_extracts))
            
            for i, image_file in enumerate(image_files):
                curr_qa_extracts = [qa_extract for qa_extract in qa_extracts if qa_extract.page_number == i + 1]
                results.append(FileExtractLLMResponse(
                                file=image_file, 
                                total_pages=total_pages, 
                                results=curr_qa_extracts))
        
        return results
        
    except Exception as e:
        logger.error(f"Error extracting QA from PDF files: {e}")
        return None

def export_qa_create_requests(files_qa_extracts: List[FileExtractLLMResponse]):
    qa_create_requests = []
    for file_extract in files_qa_extracts:
        file = file_extract.file
        for question in file_extract.results:
            options = question.options
            label = question.correct_answer

            question_create_request = QuestionCreateRequest(
                file_id=file.id,
                html_content=question.content,
                type=question.type,
                reference=question.reference,
                code=question.code,
                page_number=question.page_number,
                position_in_page=question.position_in_page
            )

            answer_create_requests = []
            
            try:
                if question.type == QuestionTypeEnum.TRUE_FALSE:
                    if label:
                        answer_create_request = AnswerCreateRequest(
                            html_content=label,
                            is_correct=label == TrueFalseAnswerEnum.TRUE,
                            label=label
                        )
                        answer_create_requests.append(answer_create_request)

                else:
                    for option in options:
                        answer_create_request = AnswerCreateRequest(
                            html_content=options[option],
                            is_correct=option == label,
                            label=option
                        )
                        answer_create_requests.append(answer_create_request)

            except Exception as e:
                answer_create_requests = []
                    
            qa_create_request = QACreateRequest(
                question=question_create_request,
                answers=answer_create_requests
            )
            qa_create_requests.append(qa_create_request)
    
    return qa_create_requests
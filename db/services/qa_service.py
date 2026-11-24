from db.common.models.question import Question
from db.common.models.answer import Answer
from db.common.models.file import File
from db.models.qa_schemas import (
    QuestionCreateRequest, 
    AnswerCreateRequest, 
    QACreateRequest,
    QAResponse,
    AnswerResponse
)
from sqlalchemy.orm import Session
from db.models.common_schemas import ApiSuccessResponse, ApiErrorResponse, ApiNotFoundErrorResponse
from typing import List
from loguru import logger
from sqlalchemy import text
from db.models.qa_schemas import QuestionTypeEnum

def create_question_to_db(db: Session, question: QuestionCreateRequest):
    try:
        db_question = Question(code=question.code, 
                                source_file_id=question.file_id, 
                                html_content=question.html_content, 
                                type=question.type, 
                                reference=question.reference,
                                page_number=question.page_number,
                                position_in_page=question.position_in_page)
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question
    except Exception as e:
        db.rollback()
        return None

def create_answers_to_db(db: Session, answers: List[AnswerCreateRequest]):
    try:
        db_answers = [Answer(question_id=answer.question_id, html_content=answer.html_content, is_correct=answer.is_correct, label=answer.label) for answer in answers]
        for answer in db_answers:
            db.add(answer)
        db.commit()
        for answer in db_answers:
            db.refresh(answer)
        return db_answers
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create answers: {e}")
        return None
    
def create_qa_to_db(db: Session, qa: QACreateRequest):
    try:
        question_create_request = qa.question
        db_question = create_question_to_db(db, question_create_request)

        if not db_question:
            db.rollback()
            return ApiErrorResponse(message="Failed to create question", status_code=500)

        if len(qa.answers) == 0:
            return ApiSuccessResponse(message="No answers provided", status_code=200)

        answer_create_requests = [AnswerCreateRequest(question_id=db_question.id, html_content=answer.html_content, is_correct=answer.is_correct, label=answer.label) for answer in qa.answers]
        db_answers = create_answers_to_db(db, answer_create_requests)
    
        if not db_answers:
            db.rollback()
            return ApiErrorResponse(message="Failed to create answers", status_code=500)

        return ApiSuccessResponse(message="QA created successfully", status_code=200)
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def delete_qa_by_collection_id(db: Session, collection_id: int):
    try:
        db_questions = db.query(Question, File) \
                        .join(File, Question.source_file_id == File.id) \
                        .filter(File.collection_id == collection_id).all()
        
        for question, _ in db_questions:
            question.is_deleted = True

        db_answers = db.query(Answer, Question, File) \
                    .join(Question, Answer.question_id == Question.id) \
                    .join(File, Question.source_file_id == File.id) \
                    .filter(File.collection_id == collection_id).all()
        
        for answer, _, _ in db_answers:
            answer.is_deleted = True

        db.commit()

        for question, _ in db_questions:
            db.refresh(question)
        for answer, _, _ in db_answers:
            db.refresh(answer)

        return ApiSuccessResponse(message="QA deleted successfully", status_code=200)
    except Exception as e:
        db.rollback()
        return ApiErrorResponse(message=str(e), status_code=500)

def get_qa_by_collection_id(db: Session, collection_id: int) -> List[QAResponse]:
    try:
        raw_query = """
            SELECT q.id AS id, q.code AS question_code, q.source_file_id AS source_file_id, q.html_content AS question_html_content, q.type AS question_type, 
            q.reference AS question_reference, q.created_at AS question_created_at, q.page_number AS question_page_number, q.position_in_page AS question_position_in_page,
            
            a.id AS answer_id, a.html_content AS answer_html_content, a.is_correct AS answer_is_correct, a.label AS answer_label, a.created_at AS answer_created_at
            FROM questions q
            LEFT JOIN answers a ON q.id = a.question_id
            LEFT JOIN files f ON q.source_file_id = f.id
            WHERE f.collection_id = :collection_id
            AND q.is_deleted = FALSE
        """
        result = db.execute(text(raw_query), {"collection_id": collection_id})
        
        # Chỉ cần một dictionary để xây dựng cấu trúc cuối cùng
        qa_map = {}
        
        # Duyệt qua kết quả MỘT LẦN DUY NHẤT
        for row in result:
            question_id = row.id
            
            # Nếu chưa gặp question này, hãy tạo đối tượng QAResponse mới
            if question_id not in qa_map:
                qa_map[question_id] = QAResponse(
                    id=row.id, 
                    source_file_id=row.source_file_id, 
                    type=QuestionTypeEnum(row.question_type), 
                    html_content=row.question_html_content, 
                    reference=row.question_reference, 
                    code=row.question_code, 
                    created_at=row.question_created_at, 
                    page_number=row.question_page_number,
                    position_in_page=row.question_position_in_page,
                    answers=[]  # Khởi tạo danh sách câu trả lời rỗng
                )
            
            if row.answer_id:
                # Bây giờ, thêm câu trả lời (answer) từ row hiện tại vào question tương ứng
                answer = AnswerResponse(
                    id=row.answer_id, 
                    html_content=row.answer_html_content, 
                    is_correct=row.answer_is_correct, 
                    label=row.answer_label, 
                    created_at=row.answer_created_at
                )
                qa_map[question_id].answers.append(answer)
        
        qa_list = list(qa_map.values())
        qa_list = [qa.to_dict() for qa in qa_list]
        return ApiSuccessResponse(message="QA fetched successfully", status_code=200, data=qa_list)

    except Exception as e:
        return ApiErrorResponse(message=str(e), status_code=500)
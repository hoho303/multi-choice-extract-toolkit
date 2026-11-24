from app.core import cfg
from app.core.prompt.prompt_manager import prompt_manager
from app.models.base import BaseSchema
from app.services.llm_service import LLMModel
from loguru import logger

class IsDocumentImageResponse(BaseSchema):
    result: bool

def is_document_image_llm(image: str, model: LLMModel) -> bool:
    user_prompt = prompt_manager.render("refine_document_image")
    print(user_prompt)
    try:
        response = model.generate_images_content(user_prompt, [image], IsDocumentImageResponse)
        print(response.text)
        response = IsDocumentImageResponse.model_validate_json(response.text)
        return response.result
    except Exception as e:
        logger.error(f"Error is document image: {e}")
        return True


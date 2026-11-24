from typing import AsyncGenerator
from google.genai.types import GenerateContentConfig, ThinkingConfig
from google import genai
from openai import OpenAI
from loguru import logger
import os
from app.models.base import BaseSchema
from typing import Any, List
from PIL import Image
from google.genai import types
from app.utils import ImageProcessor
import pathlib

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class LLMModel:

    def show_log(self, message, level: str = "info"):
        if level == "debug" and os.getenv('DEBUG'):
            logger.debug(str(message))
        elif level == "error":
            logger.error(str(message))
        else:
            logger.info(str(message))
            
    def __init__(self, model_name="gemini-2.5-flash-latest", system_prompt=None) -> None:
        self.model_name = model_name
        self.system_prompt = system_prompt

    def load_model(self):
        pass

    def streaming_content(self, user_prompt):
        pass

class GeminiModel(LLMModel):
    def __init__(self, model_name="models/gemini-flash-latest", system_prompt=None):
        super().__init__(model_name, system_prompt)
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.config = GenerateContentConfig(
            temperature=0,
            top_p=0.95,
            top_k=40,
            thinking_config=ThinkingConfig(
                thinking_budget=0
            )
        )

    def generate_content(self, user_prompt):
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[user_prompt],
            config=self.config
        )
        return response

    def generate_images_content(self, user_prompt, images: list[Image.Image] | list[str], schema: BaseSchema | None = None) -> str:
        contents = []

        for image in images:
            if isinstance(image, Image.Image):
                contents.append(image)
            elif isinstance(image, str):
                image_bytes, content_type = ImageProcessor.get_image_info_from_url(image)
                if image_bytes and content_type:
                    contents.append(types.Part.from_bytes(
                        data=image_bytes, mime_type=content_type
                    ))

        contents = [user_prompt] + contents

        if schema:
            config = self.config.model_copy(
                update={"response_mime_type": "application/json",
                        "response_json_schema": schema.model_json_schema()})
        else:
            config = self.config

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        return response

    def generate_pdf_content(self, user_prompt, pdf_path: str, schema: BaseSchema | None = None) -> str:
        filepath = pathlib.Path(pdf_path)
        
        if not filepath.exists():
            return None

        contents = types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type="application/pdf"
        )

        contents = [user_prompt] + [contents]

        if schema:
            config = self.config.model_copy(
                update={"response_mime_type": "application/json",
                        "response_json_schema": schema.model_json_schema()})
        else:
            config = self.config

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        return response

    async def streaming_content(self, user_prompt) -> AsyncGenerator[Any, None]:
        response = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=[user_prompt],
            config=self.config
        )
        for chunk in response:
            yield chunk
        
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from app.services.llm_service import GeminiModel

load_dotenv()

class Settings(BaseSettings):
    PG_USERNAME_DB: str = os.environ.get("PG_USERNAME_DB", "postgres")
    PG_PASSWORD_DB: str = os.environ.get("PG_PASSWORD_DB", "postgres")
    PG_HOST_DB: str = os.environ.get("PG_HOST_DB", "localhost")
    PG_PORT_DB: int = os.environ.get("PG_PORT_DB", 5432)
    PG_DATABASE: str = os.environ.get("PG_DATABASE", "mcq_extractor")

    REDIS_HOST: str = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT: int = os.environ.get("REDIS_PORT", 6379)

    RABBITMQ_HOST: str = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = os.environ.get("RABBITMQ_PORT", 5672)
    RABBITMQ_USER: str = os.environ.get("RABBITMQ_USER", "admin")
    RABBITMQ_PASSWORD: str = os.environ.get("RABBITMQ_PASSWORD", "admin")

    CELERY_BROKER_URL: str = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
    print(CELERY_BROKER_URL)
    CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/6"
    print(CELERY_RESULT_BACKEND)

    BASE_SAVE_DIR: str = os.environ.get("BASE_SAVE_DIR", "temp")
    os.makedirs(BASE_SAVE_DIR, exist_ok=True)

settings = Settings()
gemini_model = GeminiModel(model_name="models/gemini-flash-latest")
gemini_lite_model = GeminiModel(model_name="models/gemini-flash-lite-latest")
gemini_pro_model = GeminiModel(model_name="models/gemini-2.5-pro")
postgres_client = None

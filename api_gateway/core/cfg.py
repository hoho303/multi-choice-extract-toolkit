import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()   

class Settings(BaseSettings):
    PG_USERNAME_DB: str = os.environ.get("PG_USERNAME_DB", "postgres")
    PG_PASSWORD_DB: str = os.environ.get("PG_PASSWORD_DB", "postgres")
    PG_HOST_DB: str = os.environ.get("PG_HOST_DB", "localhost")
    PG_PORT_DB: int = os.environ.get("PG_PORT_DB", 5432)
    PG_DATABASE: str = os.environ.get("PG_DATABASE", "mcq_extractor")

    # RabbitMQ
    RABBITMQ_HOST: str = os.environ.get("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = os.environ.get("RABBITMQ_PORT", 5672)
    RABBITMQ_USER: str = os.environ.get("RABBITMQ_USER", "admin")
    RABBITMQ_PASSWORD: str = os.environ.get("RABBITMQ_PASSWORD", "admin")

    # Redis
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = os.environ.get("REDIS_PORT", 6379)

settings = Settings()
postgres_client = None
celery_app = None
redis_client = None
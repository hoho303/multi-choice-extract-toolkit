from celery import Celery
from .core import cfg
from loguru import logger
from db.common.core.database import DatabaseConnector
from app.tasks import register_extract_qa_task, register_import_files_from_web_task

# Postgres
cfg.postgres_client = DatabaseConnector(
    {
        "username_db": cfg.settings.PG_USERNAME_DB,
        "password_db": cfg.settings.PG_PASSWORD_DB,
        "host_db": cfg.settings.PG_HOST_DB,
        "port_db": cfg.settings.PG_PORT_DB,
        "database": cfg.settings.PG_DATABASE
    }, "postgres")
cfg.postgres_client.start()
print("Postgres initialized successfully")

# Khởi tạo Celery instance
celery = Celery(
    "worker",
    broker=cfg.settings.CELERY_BROKER_URL,
    backend=cfg.settings.CELERY_RESULT_BACKEND
)

# Đăng ký các tasks
register_extract_qa_task(celery)
register_import_files_from_web_task(celery)
from db.common.core.database import DatabaseConnector
from core import cfg
from core.cfg import settings
from db.init_db import init_db
from celery import Celery
from redis import asyncio as aioredis

def init_api():
    # Postgres
    cfg.postgres_client = DatabaseConnector(
        {
            "username_db": settings.PG_USERNAME_DB,
            "password_db": settings.PG_PASSWORD_DB,
            "host_db": settings.PG_HOST_DB,
            "port_db": settings.PG_PORT_DB,
            "database": settings.PG_DATABASE
        }, "postgres")
    cfg.postgres_client.start()
    print("Postgres initialized successfully")
    
    # Worker
    cfg.celery_app = Celery(
        'api-gateway',
        broker=f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//',
        backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/6'
    )
    print("Celery worker initialized successfully")

    cfg.redis_client = aioredis.Redis(host=cfg.settings.REDIS_HOST, port=cfg.settings.REDIS_PORT, db=0)
    print("Redis initialized successfully")

    init_db()
    print("Database initialized successfully")
    
    return None
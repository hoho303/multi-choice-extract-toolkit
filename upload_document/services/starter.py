from core import cfg
from core.cfg import settings
from celery import Celery
from redis import asyncio as aioredis

def init_api():
    # # Worker
    # cfg.celery_app = Celery(
    #     'api-gateway',
    #     broker=f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//',
    #     backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/6'
    # )
    # print("Celery worker initialized successfully")

    # cfg.redis_client = aioredis.Redis(host=cfg.settings.REDIS_HOST, port=cfg.settings.REDIS_PORT, db=0)
    # print("Redis initialized successfully")

    return None
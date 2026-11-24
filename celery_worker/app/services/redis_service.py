from redis import Redis
from app.core import cfg
from app.models.message_schemas import ProgressMessage

redis_client = Redis(host=cfg.settings.REDIS_HOST, port=cfg.settings.REDIS_PORT, db=0)

def publish_progress_task_by_id(channel_name: str, id: int, session_id: str, message: ProgressMessage):
    # redis_client.publish(f"{channel_name}_{session_id}_{id}", message.model_dump_json())
    print(f"Publishing message to channel: {channel_name}_{session_id}_{id}")
    redis_client.publish(f"{channel_name}_{session_id}_{id}", message.model_dump_json())

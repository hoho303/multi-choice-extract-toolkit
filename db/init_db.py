from core import cfg
from db.common.core.database import DatabaseConnector
from db.common.models.base import Base
# Import tất cả models để SQLAlchemy biết và tạo tables
from db.common.models.user import User
from db.common.models.collection import Collection
from db.common.models.file import File
from db.common.models.question import Question
from db.common.models.answer import Answer
import os
from dotenv import load_dotenv
from core import cfg

load_dotenv()

def init_db():
    Base.metadata.create_all(cfg.postgres_client.get_engine())

if __name__ == "__main__":
    init_db()
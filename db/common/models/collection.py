from .base import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
import datetime
from sqlalchemy.orm import relationship
import enum

class ProcessingStatusEnum(str, enum.Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

# TABLE collections: 
	# - id: INT, AUTO_INCREMENT, PRIMARY KEY
	# - name: VARCHAR(255), NOT NULL
	# - user_id: INT
	# - processing_status: ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'), DEFAULT 'PENDING' -- Trạng thái của task
	# - created_at: TIMESTAMP
	# - updated_at: TIMESTAMP

class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, nullable=False)
    processing_status = Column(Enum(ProcessingStatusEnum, name='processing_status_enum'), default=ProcessingStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_deleted = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'processing_status': self.processing_status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
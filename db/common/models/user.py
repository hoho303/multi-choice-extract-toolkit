import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from .base import Base

# TABLE users (Nếu hệ thống có đăng nhập)
# 	- id: INT, AUTO_INCREMENT, PRIMARY KEY
# 	- username: VARCHAR(255), UNIQUE
# 	- created_at: TIMESTAMP	

class User(Base):   
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)  
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_deleted = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
            "is_deleted": self.is_deleted
        }

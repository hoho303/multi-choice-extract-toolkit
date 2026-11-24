from .base import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
import datetime
from sqlalchemy.orm import relationship

# TABLE images:
# 	- id: INT, AUTO_INCREMENT, PRIMARY KEY
# 	- collection_id: INT, NOT NULL, FOREIGN KEY REFERENCES collections(id)
# 	- url: TEXT, NOT NULL -- Dùng TEXT để chứa được URL dài
# 	- file_order: INT, NOT NULL -- Thứ tự của trang ảnh, ví dụ: 1, 2, 3...
# 	- created_at: TIMESTAMP

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, nullable=False)
    url = Column(Text, nullable=False)
    file_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_deleted = Column(Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'collection_id': self.collection_id,
            'url': self.url,
            'file_order': self.file_order,
            'created_at': self.created_at,
            'is_deleted': self.is_deleted
        }
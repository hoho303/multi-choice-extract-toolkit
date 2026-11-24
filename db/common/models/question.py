from .base import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
import datetime
from sqlalchemy.orm import relationship

# TABLE questions
# 	- id: INT, AUTO_INCREMENT, PRIMARY KEY
# 	- code: VARCHAR(255), NOT NULL -- The ID of the question
# 	- collection_id: INT, NOT NULL, FOREIGN KEY REFERENCES collections(id)
# 	- source_file_id: INT, FOREIGN KEY REFERENCES files(id) -- QUAN TRỌNG: Truy vết nguồn gốc câu hỏi
# 	- html_content: TEXT, NOT NULL
# 	- type: ENUM('MULTIPLE_CHOICE', 'FILL_IN_THE_BLANK', 'ESSAY'), DEFAULT 'MULTIPLE_CHOICE' -- Dùng ENUM rõ ràng hơn
# 	- reference: TEXT -- The reference text or passage. Must be an empty string \"\" if not applicable

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False)
    source_file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    html_content = Column(Text, nullable=False)
    type = Column(Enum('MULTIPLE_CHOICE', 'READING_COMPREHENSION', 'TRUE_FALSE', name='question_type_enum'), default='MULTIPLE_CHOICE')
    reference = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    position_in_page = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_deleted = Column(Boolean, default=False)

    # Relationship to Answer
    answers = relationship('Answer', back_populates='question')

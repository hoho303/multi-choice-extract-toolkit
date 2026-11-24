from .base import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
import datetime
from sqlalchemy.orm import relationship

# TABLE answers
# 	- id: INT, AUTO_INCREMENT, PRIMARY KEY
# 	- question_id: INT, NOT NULL, FOREIGN KEY REFERENCES questions(id)
# 	- html_content: TEXT, NOT NULL
# 	- is_correct: BOOLEAN, DEFAULT FALSE -- QUAN TRỌNG: Xác định đáp án đúng
# 	- label: VARCHAR(10) -- Ví dụ: 'A', 'B', 'C', 'D'
# 	- created_at: TIMESTAMP

class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    html_content = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    label = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_deleted = Column(Boolean, default=False)
    
    # Relationship to Question
    question = relationship('Question', back_populates='answers')
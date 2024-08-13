from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
import datetime

Base = declarative_base()

class ProcessingStatus(enum.Enum):
    SUCCESS = "success"
    FAIL = "fail"

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    processing_result = relationship("ProcessingResult", back_populates="image", uselist=False)

class ProcessingResult(Base):
    __tablename__ = "processing_results"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    status = Column(Enum(ProcessingStatus), nullable=False)
    error_description = Column(Text, nullable=True)
    recognized_data = Column(Text, nullable=True)
    image = relationship("Image", back_populates="processing_result")

class PromptFile(Base):
    __tablename__ = "prompt_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum
import datetime
from db import Base
from models.dashboard import Project

class StatusEnum(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProcessingStatus(Base):
    __tablename__ = "processing_statuses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    progress = Column(Integer, default=0)  # percentage
    processed_files = Column(Integer, default=0)
    total_files = Column(Integer, nullable=False)
    processed_file_names = Column(Text, default="")  # Comma-separated list of filenames

    project = relationship("Project", back_populates="processing_statuses")

    def __repr__(self):
        return f"<ProcessingStatus(project_id={self.project_id}, status={self.status}, progress={self.progress})>"

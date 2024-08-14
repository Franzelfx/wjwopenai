from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship, backref
from db import Base
import datetime

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    directory_name = Column(String, nullable=False)

    processing_statuses = relationship(
        "ProcessingStatus",
        back_populates="project",
        cascade="all, delete-orphan"  # This will delete associated ProcessingStatus records when the project is deleted
    )

    def __repr__(self):
        return f"<Project(name={self.name}, created_at={self.created_at})>"

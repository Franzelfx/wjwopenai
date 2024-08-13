from sqlalchemy import Column, Integer, String, Text, DateTime
from db import Base
import datetime


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    directory_name = Column(
        String, nullable=False
    )  # Add this field to store the directory name

    def __repr__(self):
        return f"<Project(name={self.name}, created_at={self.created_at})>"

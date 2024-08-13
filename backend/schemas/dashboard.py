from pydantic import BaseModel
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: str = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import enum

class StatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProcessingStatusBase(BaseModel):
    project_id: int
    status: StatusEnum
    progress: int
    processed_files: int
    total_files: int
    processed_file_names: List[str]  # Store file names as a list

class ProcessingStatusCreate(ProcessingStatusBase):
    pass

class ProcessingStatusUpdate(BaseModel):
    progress: Optional[int] = None
    processed_files: Optional[int] = None
    processed_file_name: Optional[str] = None
    status: Optional[StatusEnum] = None

class ProcessingStatusResponse(ProcessingStatusBase):
    id: int
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""

    @validator("start_time", "end_time", pre=True, always=True)
    def datetime_to_string(cls, value):
        if value is None:
            return ""
        # When not of type string, convert to string
        if not isinstance(value, str):
            return value.strftime("%Y-%m-%d %H:%M:%S")

    class Config:
        orm_mode = True

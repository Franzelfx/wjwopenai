import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models.processing import ProcessingStatus, StatusEnum
from schemas.processing import ProcessingStatusCreate, ProcessingStatusUpdate, ProcessingStatusResponse

def create_processing_status(db: Session, status: ProcessingStatusCreate):
    db_status = ProcessingStatus(**status.dict())
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_processing_status(db: Session, status_id: int) -> Optional[ProcessingStatusResponse]:
    return db.query(ProcessingStatus).filter(ProcessingStatus.id == status_id).first()

def update_processing_status(db: Session, status_id: int, update: ProcessingStatusUpdate) -> Optional[ProcessingStatusResponse]:
    db_status = db.query(ProcessingStatus).filter(ProcessingStatus.id == status_id).first()
    if db_status:
        if update.progress is not None:
            db_status.progress = update.progress
        if update.processed_files is not None:
            db_status.processed_files = update.processed_files
        if update.processed_file_name is not None:
            db_status.processed_file_names += f"{update.processed_file_name},"
        if db_status.progress >= 100:
            db_status.status = StatusEnum.COMPLETED
            db_status.end_time = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_status)
    return db_status

def get_processing_status_by_project_id(db: Session, project_id: int):
    return db.query(ProcessingStatus).filter(ProcessingStatus.project_id == project_id).first()

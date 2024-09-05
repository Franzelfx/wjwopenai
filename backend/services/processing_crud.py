import os
import json
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.dashboard import Project
from models.processing import ProcessingStatus, StatusEnum
from schemas.processing import ProcessingStatusCreate, ProcessingStatusUpdate, ProcessingStatusResponse

# Define the base directory for the projects
PROJECTS_BASE_DIR = "projects"

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

# New CRUD Functions for File Handling

def get_json_file(db: Session, project_id: int, output_type: str, file_name: str):
    """Retrieve the JSON file content for a given project and output type."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_path = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "output", output_type)
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

def update_json_file(db: Session, project_id: int, output_type: str, file_name: str, content: str):
    """Update the JSON file content for a given project and output type."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_path = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "output", output_type)
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Convert the string content back to a dictionary
        content_dict = json.loads(content)

        # Write the JSON content with proper indentation
        with open(file_path, 'w') as file:
            json.dump(content_dict, file, indent=4)  # Indentation set to 4 spaces

        return {"status": "success", "message": f"File '{file_name}' successfully updated."}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")

def delete_json_file(db: Session, project_id: int, output_type: str, file_name: str):
    """Delete a JSON file for a given project and output type."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_path = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "output", output_type)
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_path)
        return {"status": "success", "message": f"File '{file_name}' successfully deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

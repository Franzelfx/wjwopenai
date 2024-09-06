import os
import json
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.dashboard import Project
from models.processing import ProcessingStatus, StatusEnum
from schemas.processing import ProcessingStatusCreate, ProcessingStatusUpdate, ProcessingStatusResponse
from fastapi.responses import FileResponse
from urllib.parse import unquote  # Import unquote for URL decoding
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
        with open(file_path, 'r', encoding='utf-8') as file:
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

        # Write the JSON content with proper indentation and UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(content_dict, file, indent=4, ensure_ascii=False)  # Use ensure_ascii=False to keep German characters

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

def find_file_in_directory(directory: str, target_file: str) -> Optional[str]:
    """
    Recursively search for a file in a given directory and its subdirectories.

    Args:
        directory (str): The base directory to start searching from.
        target_file (str): The name of the file to find.

    Returns:
        Optional[str]: The full path to the file if found, otherwise None.
    """
    for root, _, files in os.walk(directory):
        if target_file in files:
            return os.path.join(root, target_file)
    return None


def get_input_file(db: Session, project_id: int, file_name: str, folder_name: str):
    """Retrieve the input file content for a given project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Decode the filename
    decoded_file_name = unquote(file_name)

    # Remove "_invalid" from the file name if present
    decoded_file_name = decoded_file_name.replace("_invalid", "")

    # Define the base path for input files, starting from the "input" directory
    base_path = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input")

    # Search for the file within the input directory and all subdirectories
    file_path = find_file_in_directory(base_path, decoded_file_name)

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    print(f"Found file at: {file_path}")  # Debugging output to verify the path

    try:
        # Open the file in binary mode to handle image formats
        with open(file_path, 'rb') as file:
            return file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

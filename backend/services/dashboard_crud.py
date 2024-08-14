import os
import shutil
import zipfile
from datetime import datetime
from sqlalchemy.orm import Session
from models.dashboard import Project
from schemas.dashboard import ProjectCreate, ProjectUpdate
from fastapi import HTTPException, UploadFile
from models.processing import ProcessingStatus, StatusEnum
from services.validator import JSONValidator

# Define the base directory for the projects
PROJECTS_BASE_DIR = "projects"

def create_project(db: Session, project: ProjectCreate):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(PROJECTS_BASE_DIR, timestamp)

    try:
        create_project_directories(project_dir)
        db_project = Project(
            name=project.name,
            description=project.description,
            directory_name=timestamp,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # Automatically create a ProcessingStatus object for the new project
        create_processing_status(db, db_project.id)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to create project or directories"
        ) from e

    return db_project

def create_project_directories(project_dir: str):
    previous_umask = os.umask(0)
    try:
        os.makedirs(os.path.join(project_dir, "input"), mode=0o777, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "output", "fail"), mode=0o777, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "output", "success"), mode=0o777, exist_ok=True)
    finally:
        os.umask(previous_umask)

def create_processing_status(db: Session, project_id: int):
    db_status = ProcessingStatus(
        project_id=project_id,
        status=StatusEnum.PENDING,
        total_files=0  # This should be updated once files are added
    )
    db.add(db_status)
    db.commit()
    db.refresh(db_status)

def get_projects(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Project).offset(skip).limit(limit).all()

def update_project(db: Session, project_id: int, project: ProjectUpdate):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    db_project.name = project.name
    db_project.description = project.description
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = os.path.join(PROJECTS_BASE_DIR, db_project.directory_name)

    try:
        db.delete(db_project)
        db.commit()

        if os.path.exists(project_dir):
            delete_directory(project_dir)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to delete project or directory"
        ) from e

    return db_project

def delete_directory(directory_path: str):
    try:
        shutil.rmtree(directory_path)
    except (PermissionError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete directory: {e}")

def upload_files_to_input(db: Session, project_id: int, files: list[UploadFile]):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input")
    os.makedirs(input_dir, exist_ok=True)

    return save_uploaded_files(input_dir, files)

def save_uploaded_files(directory: str, files: list[UploadFile]):
    uploaded_files = []
    for file in files:
        file_path = os.path.join(directory, file.filename)
        os.makedirs(os.path.dirname(file_path), mode=0o777, exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)
    return uploaded_files

def delete_input_file(db: Session, project_id: int, filename: str):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_file_path = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input", filename)
    if not os.path.exists(input_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(input_file_path)
        return f"File '{filename}' successfully deleted from input directory."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

def download_output_files(db: Session, project_id: int, convert_to_csv=False):
    return zip_output_files(db, project_id, convert_to_csv, ["success", "fail"])

def download_success_output_files(db: Session, project_id: int, convert_to_csv=False):
    return zip_output_files(db, project_id, convert_to_csv, ["success"])

def download_fail_output_files(db: Session, project_id: int, convert_to_csv=False):
    return zip_output_files(db, project_id, convert_to_csv, ["fail"])

def zip_output_files(db: Session, project_id: int, convert_to_csv: bool, output_types: list[str]):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    output_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "output")
    zip_filename = f"{project.name}_output.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        for output_type in output_types:
            dir_path = os.path.join(output_dir, output_type)
            if os.path.exists(dir_path):
                add_files_to_zip(zipf, dir_path, convert_to_csv, output_dir)

    return zip_filepath

def add_files_to_zip(zipf: zipfile.ZipFile, dir_path: str, convert_to_csv: bool, base_dir: str):
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            if convert_to_csv and file.endswith(".json"):
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    json_content = json_file.read()
                filename_without_ext = os.path.splitext(file)[0]
                JSONValidator.save_cleaned_json(root, filename_without_ext, json_content, convert_to_csv=True)
                file_path = os.path.join(root, f"{filename_without_ext}.csv")
            zipf.write(file_path, os.path.relpath(file_path, base_dir))

def get_file_tree(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input")
    output_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "output")

    file_tree = {
        "input": get_directory_structure(input_dir),
        "output": {
            "success": get_directory_structure(os.path.join(output_dir, "success")),
            "fail": get_directory_structure(os.path.join(output_dir, "fail")),
        },
    }

    return file_tree

def get_directory_structure(rootdir: str) -> dict:
    structure = {}
    for item in os.listdir(rootdir):
        item_path = os.path.join(rootdir, item)
        if os.path.isdir(item_path):
            structure[item] = get_directory_structure(item_path)
        else:
            structure[item] = None
    return structure

def delete_all_input_files(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input")

    if not os.path.exists(input_dir):
        raise HTTPException(status_code=404, detail="Input directory not found")

    try:
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return "All input files deleted successfully."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete files: {str(e)}")

def delete_input_file_or_folder(db: Session, project_id: int, path: str):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_path = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input", path)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File or folder not found")

    try:
        if os.path.isfile(input_path):
            os.remove(input_path)
        elif os.path.isdir(input_path):
            shutil.rmtree(input_path)
        return f"'{path}' successfully deleted from input directory."
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete '{path}': {str(e)}"
        )

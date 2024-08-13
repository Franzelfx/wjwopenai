import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from models.dashboard import Project
from schemas.dashboard import ProjectCreate, ProjectUpdate
from fastapi import HTTPException
import zipfile
from fastapi import UploadFile


# Define the base directory for the projects
PROJECTS_BASE_DIR = "projects"


def create_project(db: Session, project: ProjectCreate):
    """
    Create a new project in the database and set up the corresponding directories.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(PROJECTS_BASE_DIR, timestamp)

    try:
        # Create directories with 777 permissions
        os.makedirs(project_dir, mode=0o777, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "input"), mode=0o777, exist_ok=True)
        os.makedirs(
            os.path.join(project_dir, "output", "fail"), mode=0o777, exist_ok=True
        )
        os.makedirs(
            os.path.join(project_dir, "output", "success"), mode=0o777, exist_ok=True
        )

        db_project = Project(
            name=project.name,
            description=project.description,
            directory_name=timestamp,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        print(f"Project {db_project.name} committed to the database.")

    except Exception as e:
        db.rollback()
        print(f"Failed to create project: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create project or directories"
        )

    return db_project


def get_projects(db: Session, skip: int = 0, limit: int = 10):
    """
    Retrieve a list of projects from the database, with optional pagination.
    """
    return db.query(Project).offset(skip).limit(limit).all()


def update_project(db: Session, project_id: int, project: ProjectUpdate):
    """
    Update the details of an existing project without renaming the directory since the directory
    name is based on the creation timestamp.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    db_project.name = project.name
    db_project.description = project.description
    db.commit()
    db.refresh(db_project)

    # Since the directory name is based on the timestamp, we do not need to rename the directory.
    # Just return the updated project information.
    return db_project


def delete_project(db: Session, project_id: int):
    """
    Delete a project from the database and remove the corresponding directory.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = os.path.join(PROJECTS_BASE_DIR, db_project.directory_name)

    try:
        db.delete(db_project)
        db.commit()
        print(f"Project {db_project.name} deleted from database.")

        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            print(f"Directory {project_dir} removed successfully.")
        else:
            print(f"Directory {project_dir} does not exist or was already removed.")

    except Exception as e:
        print(f"Exception occurred during directory deletion: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to delete project or directory"
        )

    return db_project


def upload_files_to_input(db: Session, project_id: int, files):
    """
    Upload multiple files to the input directory of a specific project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input")
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)

    uploaded_files = []
    for file in files:
        file_path = os.path.join(input_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)

    return uploaded_files


def upload_folder_to_input(db: Session, project_id: int, files: list[UploadFile]):
    """
    Upload a folder to the input directory of a specific project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "input")
    if not os.path.exists(input_dir):
        os.makedirs(input_dir, mode=0o777, exist_ok=True)

    uploaded_files = []
    for file in files:
        # Ensure the directory structure exists with 777 permissions
        file_path = os.path.join(input_dir, file.filename)
        os.makedirs(os.path.dirname(file_path), mode=0o777, exist_ok=True)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)

    return uploaded_files


def delete_input_file(db: Session, project_id: int, filename: str):
    """
    Delete a specific file from the input directory of a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    input_file_path = os.path.join(
        PROJECTS_BASE_DIR, project.directory_name, "input", filename
    )
    if not os.path.exists(input_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(input_file_path)
        return f"File '{filename}' successfully deleted from input directory."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


def download_output_files(db: Session, project_id: int):
    """
    Download all output files (success and fail) as a zip.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    output_dir = os.path.join(PROJECTS_BASE_DIR, project.directory_name, "output")
    success_dir = os.path.join(output_dir, "success")
    fail_dir = os.path.join(output_dir, "fail")

    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Output directory not found")

    zip_filename = f"{project.name}_output.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        for root, _, files in os.walk(success_dir):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), output_dir),
                )

        for root, _, files in os.walk(fail_dir):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), output_dir),
                )

    return zip_filepath


def get_file_tree(db: Session, project_id: int):
    """
    Get the file tree of the input, output/success, and output/fail directories.
    """
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
    """
    Recursively builds a nested dictionary that represents the folder structure of rootdir.
    """
    structure = {}
    for item in os.listdir(rootdir):
        item_path = os.path.join(rootdir, item)
        if os.path.isdir(item_path):
            structure[item] = get_directory_structure(item_path)
        else:
            structure[item] = None
    return structure


def delete_all_input_files(db: Session, project_id: int):
    """
    Delete all files in the input directory of a specific project.
    """
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
    """
    Delete a specific file or folder from the input directory of a project.
    """
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

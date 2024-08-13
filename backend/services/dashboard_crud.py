import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from models.dashboard import Project
from schemas.dashboard import ProjectCreate, ProjectUpdate
from fastapi import HTTPException
import zipfile

# Define the base directory for the projects
PROJECTS_BASE_DIR = "projects"


def create_project(db: Session, project: ProjectCreate):
    """
    Create a new project in the database and set up the corresponding directories.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(PROJECTS_BASE_DIR, timestamp)

    try:
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, "input"))
        os.makedirs(os.path.join(project_dir, "output", "fail"))
        os.makedirs(os.path.join(project_dir, "output", "success"))

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
    Update the details of an existing project and rename the corresponding directory if needed.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    old_project_name = db_project.name
    db_project.name = project.name
    db_project.description = project.description
    db.commit()
    db.refresh(db_project)

    old_project_dir = os.path.join(PROJECTS_BASE_DIR, old_project_name)
    new_project_dir = os.path.join(PROJECTS_BASE_DIR, db_project.name)

    if old_project_name != project.name:
        try:
            if os.path.exists(old_project_dir):
                os.rename(old_project_dir, new_project_dir)
            else:
                raise HTTPException(
                    status_code=500, detail="Old project directory does not exist"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Failed to rename project directory"
            )

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

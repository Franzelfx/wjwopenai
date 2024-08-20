from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from services import dashboard_crud
from schemas.dashboard import ProjectCreate, ProjectUpdate, Project
from db import get_db
from typing import List
from fastapi.responses import FileResponse
import os
from fastapi import Query

router = APIRouter()

# Project CRUD Operations


@router.post("/", response_model=Project)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    return dashboard_crud.create_project(db=db, project=project)


@router.get("/", response_model=List[Project])
def read_projects(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return dashboard_crud.get_projects(db, skip=skip, limit=limit)


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int, project: ProjectUpdate, db: Session = Depends(get_db)
):
    return dashboard_crud.update_project(db=db, project_id=project_id, project=project)


@router.delete("/{project_id}", response_model=Project)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    return dashboard_crud.delete_project(db=db, project_id=project_id)


# File Management Operations
@router.post("/projects/{project_id}/upload", response_model=List[str])
def upload_files_to_input(
    project_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    return dashboard_crud.upload_files_to_input(
        db=db, project_id=project_id, files=files
    )

@router.get("/projects/{project_id}/file_tree")
def get_file_tree(project_id: int, db: Session = Depends(get_db)):
    return dashboard_crud.get_file_tree(db=db, project_id=project_id)

@router.post("/projects/{project_id}/upload_folder")
def upload_folder(
    project_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    return dashboard_crud.upload_folder_to_input(
        db=db, project_id=project_id, files=files
    )

@router.get("/projects/{project_id}/download_output", response_class=FileResponse)
def download_output_files(
    project_id: int,
    db: Session = Depends(get_db),
    convert_to_csv: bool = Query(False, description="Convert JSON to CSV before downloading")
):
    zip_filepath = dashboard_crud.download_output_files(db=db, project_id=project_id, convert_to_csv=convert_to_csv)
    return FileResponse(zip_filepath, filename=os.path.basename(zip_filepath))


@router.get("/projects/{project_id}/download_success_output", response_class=FileResponse)
def download_success_output_files(
    project_id: int,
    db: Session = Depends(get_db),
    convert_to_csv: bool = Query(False, description="Convert JSON to CSV before downloading")
):
    zip_filepath = dashboard_crud.download_success_output_files(
        db=db, project_id=project_id, convert_to_csv=convert_to_csv
    )
    return FileResponse(zip_filepath, filename=os.path.basename(zip_filepath))


@router.get("/projects/{project_id}/download_fail_output", response_class=FileResponse)
def download_fail_output_files(
    project_id: int,
    db: Session = Depends(get_db),
    convert_to_csv: bool = Query(False, description="Convert JSON to CSV before downloading")
):
    zip_filepath = dashboard_crud.download_fail_output_files(
        db=db, project_id=project_id, convert_to_csv=convert_to_csv
    )
    return FileResponse(zip_filepath, filename=os.path.basename(zip_filepath))

# Add this endpoint to handle DELETE requests for specific files or folders
@router.delete("/projects/{project_id}/input_files/{path:path}", response_model=str)
def delete_input_file_or_folder(
    project_id: int,
    path: str,
    db: Session = Depends(get_db)
):
    return dashboard_crud.delete_input_file_or_folder(db=db, project_id=project_id, path=path)

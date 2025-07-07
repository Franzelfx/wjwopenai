from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from services import dashboard_crud
from schemas.dashboard import ProjectCreate, ProjectUpdate, Project
from db import get_db
from typing import List
from fastapi.responses import FileResponse
import os
from fastapi import Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from schemas.dashboard import Project as ProjectSchema

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


@router.get("/projects/{project_id}/download_success_output", response_class=StreamingResponse)
def download_success_output_files(
    project_id: int,
    db: Session = Depends(get_db),
    convert_to_csv: bool = Query(True, description="Convert JSON to CSV before downloading")
):
    """
    Endpoint to download a combined CSV file from the successful output files.
    """
    # Generate the combined CSV file
    csv_filepath = dashboard_crud.create_combined_csv(db=db, project_id=project_id, output_type="success")

    # Open the CSV file for streaming
    def iterfile():
        with open(csv_filepath, mode="r", encoding="utf-8") as file:
            yield from file

    # Return CSV as a StreamingResponse
    return StreamingResponse(iterfile(), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=combined_success_output.csv"
    })

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

@router.get("/projects/{project_id}/download_success_excel")
async def download_success_excel_files(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint to download an Excel file with marked cells from the successful output files.
    """
    # Generate the Excel file and get its stream
    excel_stream = dashboard_crud.generate_excel_for_project(db=db, project_id=project_id, output_type="success")

    # Return the file as a streaming response
    return StreamingResponse(
        excel_stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={project_id}_success_output.xlsx"}
    )



@router.get("/projects/{project_id}/download_fail_excel")
async def download_fail_excel_files(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint to download an Excel file with marked cells from the failed output files.
    """
    # Generate the Excel file and get its stream
    excel_stream = dashboard_crud.generate_excel_for_project(db=db, project_id=project_id, output_type="fail")

    # Return the file as a streaming response
    return StreamingResponse(
        excel_stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={project_id}_fail_output.xlsx"}
    )

@router.post("/projects/{project_id}/prompt")
def upload_prompt_markdown(
    project_id: int,
    md_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return dashboard_crud.upload_prompt_md(db=db, project_id=project_id, md_file=md_file)

# ── Download ───────────────────────────────────────────────────
@router.get("/projects/{project_id}/prompt", response_class=FileResponse)
def download_prompt_markdown(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None or not project.prompt_md:
        raise HTTPException(status_code=404, detail="Prompt not found")

    file_path = os.path.join(
        "projects", project.directory_name, project.prompt_md
    )
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Prompt file missing on disk")

    return FileResponse(file_path, filename=project.prompt_md)

@router.get("/projects/{project_id}", response_model=ProjectSchema)
def read_project(project_id: int, db: Session = Depends(get_db)):
    return dashboard_crud.get_project_by_id(db, project_id)
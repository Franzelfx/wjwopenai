# processing router for handling processing status
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services import processing_crud
from db import get_db
from schemas.processing import ProcessingStatusResponse
from fastapi.responses import StreamingResponse
import time
import json
from schemas.processing import ProcessingStatusResponse
from models.processing import StatusEnum
from loguru import logger

router = APIRouter()

@router.get("/status/project/{project_id}", response_model=ProcessingStatusResponse)
def get_status_by_project(project_id: int, db: Session = Depends(get_db)):
    status = processing_crud.get_processing_status_by_project_id(db=db, project_id=project_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Processing status not found for the project")
    
    # Ensure processed_file_names is a list
    processed_file_names_list = status.processed_file_names.strip(",").split(",") if status.processed_file_names else []

    # Convert the StatusEnum to its value (string)
    valid_status = status.status.value if isinstance(status.status, StatusEnum) else StatusEnum.PENDING.value

    return ProcessingStatusResponse(
        id=status.id,
        project_id=status.project_id,
        status=valid_status,  # Pass the status as a string
        progress=status.progress,
        processed_files=status.processed_files,
        total_files=status.total_files,
        processed_file_names=processed_file_names_list,
        start_time=status.start_time,  # This will be automatically converted by the validator
        end_time=status.end_time  # This will be automatically converted by the validator
    )

@router.get("/status/project/{project_id}/sse")
async def status_sse_by_project(project_id: int, db: Session = Depends(get_db)):
    def event_generator():
        while True:
            status = processing_crud.get_processing_status_by_project_id(db=db, project_id=project_id)
            if status is None:
                yield "event: error\ndata: Status not found\n\n"
                break

            # Ensure processed_file_names is a list
            processed_file_names_list = status.processed_file_names.strip(",").split(",") if status.processed_file_names else []

            # Convert the StatusEnum to its value (string)
            valid_status = status.status.value if isinstance(status.status, StatusEnum) else StatusEnum.PENDING.value

            data = {
                "status": valid_status,  # Pass the status as a string
                "progress": status.progress,
                "processed_files": status.processed_files,
                "total_files": status.total_files,
                "processed_file_names": processed_file_names_list,
                "start_time": status.start_time.strftime("%Y-%m-%d %H:%M:%S") if status.start_time else "",
                "end_time": status.end_time.strftime("%Y-%m-%d %H:%M:%S") if status.end_time else "",
            }

            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(2)  # Adjust based on how often you want updates

    return StreamingResponse(event_generator(), media_type="text/event-stream")
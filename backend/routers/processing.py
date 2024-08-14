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
from services.engine import OCRProcessor  # Import the OCRProcessor class
from models.processing import ProcessingStatus

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

@router.post("/start-ocr/{project_id}")
def start_ocr_process(project_id: int, db: Session = Depends(get_db)):
    logger.info(f"Starting OCR process for project {project_id}")
    try:
        ocr_processor = OCRProcessor(project_id, db)
        ocr_processor.process_images()
        logger.info(f"OCR process completed successfully for project {project_id}")
        return {"status": "success", "message": "OCR process completed successfully"}
    except Exception as e:
        logger.error(f"OCR process failed for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR process failed: {str(e)}")

@router.post("/stop-ocr/{project_id}")
def stop_ocr_process(project_id: int, db: Session = Depends(get_db)):
    logger.info(f"Stopping OCR process for project {project_id}")
    try:
        ocr_processor = OCRProcessor.get_processor(project_id)
        if not ocr_processor:
            raise HTTPException(status_code=404, detail="OCR Processor not found for this project.")
        ocr_processor.stop_processing()
        return {"status": "success", "message": "OCR process stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop OCR process for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop OCR process: {str(e)}")

@router.post("/resume-ocr/{project_id}")
def resume_ocr_process(project_id: int, db: Session = Depends(get_db)):
    logger.info(f"Resuming OCR process for project {project_id}")
    try:
        ocr_processor = OCRProcessor.get_processor(project_id)
        if not ocr_processor:
            raise HTTPException(status_code=404, detail="OCR Processor not found for this project.")
        ocr_processor.resume_processing()
        return {"status": "success", "message": "OCR process resumed successfully"}
    except Exception as e:
        logger.error(f"Failed to resume OCR process for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume OCR process: {str(e)}")

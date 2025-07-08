"""processing.py
Refactored FastAPI router for OCR start/stop/resume with
syntax‑error‑free, fully async‑safe background task handling.
"""

from __future__ import annotations

import io
import json
import time
import datetime
from typing import Any, Dict, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.orm import Session

from db import get_db, SessionLocal
from models.processing import StatusEnum
from schemas.processing import ProcessingStatusResponse
from fastapi.responses import JSONResponse
from services import processing_crud
from services.engine import OCRProcessor
import asyncio

# ────────────────────────────────────────────
# Router + in‑memory task registry
# ────────────────────────────────────────────
router = APIRouter()
ocr_tasks: Dict[int, Dict[str, Any]] = {}


async def _run_ocr(project_id: int, db_session: Session) -> None:
    """Background coroutine that executes OCR for one project."""
    proc: Optional[OCRProcessor] = None
    try:
        proc = OCRProcessor(project_id, db_session)
        await proc.process_images()  # may pause/stop internally
    except Exception as exc:
        logger.exception(f"OCR failed for project {project_id}: {exc}")
        if proc:
            proc.update_processing_status(StatusEnum.FAILED, proc.processing_status.progress)
    finally:
        if proc:
            proc.close()
        db_session.close()
        ocr_tasks.pop(project_id, None)  # deregister


# ────────────────────────────────────────────
# CRUD‑style endpoints
# ────────────────────────────────────────────

@router.post("/start-ocr/{project_id}", status_code=202)
async def start_ocr_process(project_id: int, db: Session = Depends(get_db)):
    """Kick off OCR in the background."""
    if (existing := ocr_tasks.get(project_id)) and not existing["task"].done():
        raise HTTPException(400, "OCR already running for this project")

    status = processing_crud.get_processing_status_by_project_id(db, project_id)
    if not status:
        raise HTTPException(404, "Processing status not found")
    if status.status not in (StatusEnum.PENDING, StatusEnum.FAILED):
        raise HTTPException(400, f"Cannot start OCR when status is {status.status.value}")

    status.start_time = datetime.datetime.utcnow()
    status.status = StatusEnum.IN_PROGRESS
    status.progress = 0
    db.commit()

    bg_db = SessionLocal()
    task = asyncio.create_task(_run_ocr(project_id, bg_db))
    ocr_tasks[project_id] = {"task": task}
    logger.info(f"OCR started for project {project_id}")
    return {"status": "started", "project_id": project_id}


@router.post("/stop-ocr/{project_id}")
async def stop_ocr_process(project_id: int):
    """Request graceful stop of a running OCR task."""
    entry = ocr_tasks.get(project_id)
    if not entry:
        raise HTTPException(404, "No running OCR process for this project")

    proc = OCRProcessor.get_processor(project_id)
    if proc:
        proc.stop_processing()
        logger.info(f"Stop signal sent for project {project_id}")
        return {"status": "stopping", "project_id": project_id}

    # processor vanished → cancel task
    entry["task"].cancel()
    ocr_tasks.pop(project_id, None)
    raise HTTPException(500, "OCR process in undefined state; task cancelled")


@router.post("/resume-ocr/{project_id}", status_code=202)
async def resume_ocr_process(project_id: int):
    """Resume a paused OCR job."""
    if (existing := ocr_tasks.get(project_id)) and not existing["task"].done():
        raise HTTPException(400, "OCR already running for this project")

    db = SessionLocal()
    status = processing_crud.get_processing_status_by_project_id(db, project_id)
    if not status or status.status != StatusEnum.PAUSED:
        db.close()
        raise HTTPException(404, "No paused OCR to resume")

    task = asyncio.create_task(_run_ocr(project_id, db))
    ocr_tasks[project_id] = {"task": task}
    logger.info(f"OCR resumed for project {project_id}")
    return {"status": "resumed", "project_id": project_id}


@router.get("/status/project/{project_id}", response_model=ProcessingStatusResponse)
def get_status_by_project(project_id: int, db: Session = Depends(get_db)):
    status = processing_crud.get_processing_status_by_project_id(db, project_id)
    if not status:
        raise HTTPException(404, "Processing status not found for the project")

    processed = status.processed_file_names.strip(",").split(",") if status.processed_file_names else []
    return ProcessingStatusResponse(
        id=status.id,
        project_id=status.project_id,
        status=status.status.value,
        progress=status.progress,
        processed_files=status.processed_files,
        total_files=status.total_files,
        processed_file_names=processed,
        start_time=status.start_time,
        end_time=status.end_time,
    )


@router.get("/status/project/{project_id}/sse")
async def status_sse_by_project(project_id: int):
    """SSE stream of live processing status."""
    def event_gen():
        while True:
            try:
                db = SessionLocal()
                stat = processing_crud.get_processing_status_by_project_id(db, project_id)
                db.close()
                if not stat:
                    yield "event: error\ndata: Status not found\n\n"
                    break

                payload = {
                    "status": stat.status.value,
                    "progress": stat.progress,
                    "processed_files": stat.processed_files,
                    "total_files": stat.total_files,
                    "processed_file_names": stat.processed_file_names.strip(",").split(",") if stat.processed_file_names else [],
                    "start_time": stat.start_time.strftime("%Y-%m-%d %H:%M:%S") if stat.start_time else "",
                    "end_time": stat.end_time.strftime("%Y-%m-%d %H:%M:%S") if stat.end_time else "",
                }
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(2)
                yield "event: heartbeat\ndata: keep-alive\n\n"
            except Exception as exc:
                yield f"event: error\ndata: {str(exc)}\n\n"
                break

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ────────────────────────────────────────────
# JSON result-file CRUD
# ────────────────────────────────────────────
@router.get("/get-json-file/{project_id}/{output_type}/{file_name}",
            response_class=JSONResponse)
async def get_json_file(project_id: int,
                        output_type: str,
                        file_name: str,
                        db: Session = Depends(get_db)):
    """Retrieve a JSON result file as raw JSON."""
    decoded = unquote(file_name)
    data = processing_crud.get_json_file(db, project_id, output_type, decoded)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass  # already JSON string
    return JSONResponse(content=data)


@router.put("/update-json-file/{project_id}/{output_type}/{file_name}",
            response_class=JSONResponse)
async def update_json_file(project_id: int,
                           output_type: str,
                           file_name: str,
                           content: dict = Body(...),
                           db: Session = Depends(get_db)):
    """Update a JSON result file and return the updated content."""
    decoded = unquote(file_name)
    logger.info(f"Updating {decoded} ({output_type}) for project {project_id}")
    updated = processing_crud.update_json_file(db,
                                               project_id,
                                               output_type,
                                               decoded,
                                               json.dumps(content))
    return JSONResponse(content=updated)


@router.delete("/delete-json-file/{project_id}/{output_type}/{file_name}",
               response_class=JSONResponse)
async def delete_json_file(project_id: int,
                           output_type: str,
                           file_name: str,
                           db: Session = Depends(get_db)):
    """Delete a JSON result file."""
    decoded = unquote(file_name)
    deleted = processing_crud.delete_json_file(db,
                                               project_id,
                                               output_type,
                                               decoded)
    return JSONResponse(content=deleted)


# ────────────────────────────────────────────
# Original input-file retrieval
# ────────────────────────────────────────────
@router.get("/get-input-file/{project_id}/{file_name}",
            response_class=StreamingResponse)
async def get_input_file_endpoint(project_id: int,
                                  file_name: str,
                                  db: Session = Depends(get_db)):
    """Retrieve an original uploaded input file."""
    decoded = unquote(file_name)
    folder = decoded.split("_")[0].split(" ")[0]       # derive subfolder
    content = processing_crud.get_input_file(db,
                                             project_id,
                                             decoded,
                                             folder)
    mime = "application/octet-stream"
    lower = decoded.lower()
    if lower.endswith((".png", ".jpg", ".jpeg",
                       ".tif", ".tiff")):
        mime = f"image/{lower.rsplit('.', 1)[1]}"
    return StreamingResponse(io.BytesIO(content),
                             media_type=mime)
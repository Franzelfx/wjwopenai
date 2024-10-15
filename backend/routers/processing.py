from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services import processing_crud
from db import get_db
from schemas.processing import ProcessingStatusResponse, JsonFile
from fastapi.responses import StreamingResponse
from urllib.parse import unquote  # Import unquote for URL decoding
import time
import json
from schemas.processing import ProcessingStatusResponse
from models.processing import StatusEnum
from loguru import logger
from services.engine import OCRProcessor  # Import the OCRProcessor class
from fastapi import Body
import io
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

router = APIRouter()

# Constants from the .env file
CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './backend/tools/geodata/json')
CHROMA_COLLECTION_NAME = "vector_store"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def find_addresses(data: dict) -> List[str]:
    """
    Recursively search for "Adresse" in the nested JSON structure and return all found addresses.
    """
    addresses = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() == "adresse":  # Case-insensitive match for "Adresse"
                addresses.append(value)
            elif isinstance(value, dict):
                addresses.extend(find_addresses(value))  # Recursively search in nested dictionaries
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        addresses.extend(find_addresses(item))

    return addresses

@router.get("/status/project/{project_id}", response_model=ProcessingStatusResponse)
def get_status_by_project(project_id: int, db: Session = Depends(get_db)):
    status = processing_crud.get_processing_status_by_project_id(db=db, project_id=project_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Processing status not found for the project")
    
    processed_file_names_list = status.processed_file_names.strip(",").split(",") if status.processed_file_names else []
    valid_status = status.status.value if isinstance(status.status, StatusEnum) else StatusEnum.PENDING.value

    return ProcessingStatusResponse(
        id=status.id,
        project_id=status.project_id,
        status=valid_status,
        progress=status.progress,
        processed_files=status.processed_files,
        total_files=status.total_files,
        processed_file_names=processed_file_names_list,
        start_time=status.start_time,
        end_time=status.end_time
    )


@router.post("/start-ocr/{project_id}")
async def start_ocr_process(project_id: int, db: Session = Depends(get_db)):
    """
    API Endpoint to start the OCR process for a project and query the vector store to validate information like addresses.
    """
    logger.info(f"Starting OCR process for project {project_id}")
    try:
        # Initialize OCR Processor for the given project
        ocr_processor = OCRProcessor(project_id, db)
        
        # Process all images for OCR
        await ocr_processor.process_images()
        logger.info(f"OCR process completed successfully for project {project_id}")
        
        # Post-processing: Extract addresses from the processed JSON files
        extracted_addresses = []

        # Traverse all JSON files in the output directory to find "Adresse" fields
        for json_file in os.listdir(ocr_processor.output_dir):
            if json_file.endswith(".json"):
                with open(os.path.join(ocr_processor.output_dir, json_file), 'r') as f:
                    content = json.load(f)
                    # Find all addresses in the JSON content
                    addresses = find_addresses(content)
                    extracted_addresses.extend(addresses)

        # Query the vector store to validate extracted addresses
        validation_results = []
        for address in extracted_addresses:
            query_result = ocr_processor.query_vector_store(query=address, n_results=5)
            validation_results.append({
                "address": address,
                "validation_results": query_result
            })
        
        logger.info(f"Validation with vector store completed for project {project_id}")
        
        return {
            "status": "success",
            "message": "OCR process and vector store validation completed successfully",
            "ocr_results": extracted_addresses,
            "vector_store_validation": validation_results
        }
    
    except Exception as e:
        logger.error(f"OCR process failed for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR process failed: {str(e)}")

@router.post("/stop-ocr/{project_id}")
def stop_ocr_process(project_id: int, db: Session = Depends(get_db)):
    logger.info(f"Stopping OCR process for project {project_id}")
    try:
        # Retrieve the OCR processor instance
        ocr_processor = OCRProcessor.get_processor(project_id, db)
        
        # Stop the processing
        ocr_processor.stop_processing()
        
        return {"status": "success", "message": "OCR process stopped successfully"}
    
    except Exception as e:
        logger.error(f"Failed to stop OCR process for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop OCR process: {str(e)}")

@router.post("/processing/generate-vector-store")
def generate_vector_store_from_folder(project_id: int, db: Session = Depends(get_db)):
    """API endpoint to generate vector store for a specific project."""
    try:
        # Initialize the OCR processor with the project ID
        ocr_processor = OCRProcessor(project_id=project_id, db=db)
        ocr_processor.generate_vector_store()
        return {"message": f"Vector store generation completed successfully for project {project_id}."}
    except Exception as e:
        logger.error(f"Failed to generate vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate vector store: {str(e)}")


@router.get("/processing/query-vector-store")
def query_vector_store(project_id: int, query: str, n_results: int = 5, db: Session = Depends(get_db)):
    """API endpoint to query vector store for a specific project."""
    try:
        ocr_processor = OCRProcessor(project_id=project_id, db=db)
        results = ocr_processor.query_vector_store(query=query, n_results=n_results)
        if results:
            return {"results": results}
        return {"message": "No relevant documents found."}
    except Exception as e:
        logger.error(f"Failed to query vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to query vector store: {str(e)}")


@router.get("/get-json-file/{project_id}/{output_type}/{file_name}")
def get_json_file(project_id: int, output_type: str, file_name: str, db: Session = Depends(get_db)):
    """Endpoint to retrieve the content of a JSON file."""
    decoded_file_name = unquote(file_name)
    return processing_crud.get_json_file(db, project_id, output_type, decoded_file_name)


@router.put("/update-json-file/{project_id}/{output_type}/{file_name}")
def update_json_file(
    project_id: int,
    output_type: str,
    file_name: str,
    content: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Endpoint to update the content of a JSON file."""
    decoded_file_name = unquote(file_name)
    logger.info(f"Updating file: {decoded_file_name} for project {project_id}, output type {output_type}")
    
    return processing_crud.update_json_file(db, project_id, output_type, decoded_file_name, json.dumps(content))


@router.delete("/delete-json-file/{project_id}/{output_type}/{file_name}")
def delete_json_file(project_id: int, output_type: str, file_name: str, db: Session = Depends(get_db)):
    """Endpoint to delete a JSON file."""
    decoded_file_name = unquote(file_name)
    return processing_crud.delete_json_file(db, project_id, output_type, decoded_file_name)


@router.get("/get-input-file/{project_id}/{file_name}", response_class=StreamingResponse)
def get_input_file_endpoint(project_id: int, file_name: str, db: Session = Depends(get_db)):
    """Endpoint to retrieve the content of an input file."""
    decoded_file_name = unquote(file_name)
    folder_name = decoded_file_name.split('_')[0].split(' ')[0]
    file_content = processing_crud.get_input_file(db, project_id, decoded_file_name, folder_name)

    content_type = "application/octet-stream"
    if file_name.lower().endswith(('png', 'jpeg', 'jpg', 'tif', 'tiff')):
        content_type = f"image/{file_name.split('.')[-1].lower()}"

    return StreamingResponse(io.BytesIO(file_content), media_type=content_type)

@router.get("/status/project/{project_id}/sse")
async def status_sse_by_project(project_id: int, db: Session = Depends(get_db)):
    def event_generator():
        while True:
            try:
                # Fetch the latest status from the database
                db = next(get_db())  # Re-fetch the DB session to ensure the latest data
                status = processing_crud.get_processing_status_by_project_id(db=db, project_id=project_id)
                
                if status is None:
                    yield "event: error\ndata: Status not found\n\n"
                    break

                # Convert the StatusEnum to its value (string)
                valid_status = status.status.value if isinstance(status.status, StatusEnum) else StatusEnum.PENDING.value
                data = {
                    "status": valid_status,
                    "progress": status.progress,
                    "processed_files": status.processed_files,
                    "total_files": status.total_files,
                    "processed_file_names": status.processed_file_names.strip(",").split(",") if status.processed_file_names else [],
                    "start_time": status.start_time.strftime("%Y-%m-%d %H:%M:%S") if status.start_time else "",
                    "end_time": status.end_time.strftime("%Y-%m-%d %H:%M:%S") if status.end_time else "",
                }
                # Send the updated data to the client
                yield f"data: {json.dumps(data)}\n\n"

                # Send a heartbeat message every 10 seconds
                time.sleep(2)  # Data update interval
                yield f"event: heartbeat\ndata: keep-alive\n\n"
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
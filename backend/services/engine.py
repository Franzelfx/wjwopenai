import os
import json
import datetime
import base64
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.processing import ProcessingStatus, StatusEnum
from models.dashboard import Project
from loguru import logger

# Constants
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".tif", ".tiff"]
OPENAI_API_KEY = "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"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Configure OpenAI API key
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

class OCRProcessor:
    def __init__(self, project_id: int, db: Session):
        self.db = db
        self.project = self.get_project(project_id)
        self.input_dir = f"projects/{self.project.directory_name}/input"
        self.success_dir = f"projects/{self.project.directory_name}/output/success"
        self.fail_dir = f"projects/{self.project.directory_name}/output/fail"
        self.processing_status = self.get_processing_status(project_id)
        self.update_processing_status(StatusEnum.IN_PROGRESS, 0, start_time=datetime.datetime.utcnow())
        logger.info(f"OCRProcessor initialized for project {self.project.directory_name}")

    def get_project(self, project_id: int) -> Project:
        logger.debug(f"Fetching project with ID {project_id}")
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project with ID {project_id} not found")
            raise Exception(f"Project with ID {project_id} not found")
        return project

    def get_processing_status(self, project_id: int) -> ProcessingStatus:
        logger.debug(f"Fetching processing status for project {project_id}")
        status = self.db.query(ProcessingStatus).filter(ProcessingStatus.project_id == project_id).first()
        if not status:
            logger.error(f"Processing status not found for project {project_id}")
            raise Exception(f"Processing status not found for project {project_id}")
        return status

    def update_processing_status(self, status: StatusEnum, progress: int, start_time: Optional[datetime.datetime] = None, end_time: Optional[datetime.datetime] = None):
        logger.debug(f"Updating processing status to {status}, progress: {progress}%")
        if start_time:
            self.processing_status.start_time = start_time
        if end_time:
            self.processing_status.end_time = end_time

        self.processing_status.status = status
        self.processing_status.progress = progress
        self.db.commit()
        self.db.refresh(self.processing_status)

    def list_image_files(self) -> List[str]:
        logger.debug(f"Listing image files in {self.input_dir}")
        image_files = []
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if Path(file).suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    full_path = os.path.join(root, file)
                    image_files.append(full_path)
                    logger.info(f"Found image file: {full_path}")
        
        if not image_files:
            logger.warning("No image files found in input directory.")
        return image_files

    def process_images(self):
        images = self.list_image_files()
        total_files = len(images)
        logger.info(f"Total images found for processing: {total_files}")
        
        if total_files == 0:
            self.update_processing_status(StatusEnum.FAILED, 100, end_time=datetime.datetime.utcnow())
            logger.error("No images found for processing.")
            raise Exception("No images found for processing.")

        for index, image_path in enumerate(images):
            logger.info(f"Processing image {index + 1}/{total_files}: {image_path}")
            try:
                response_json = self.call_openai_api(image_path)
                if response_json:
                    self.save_output(self.success_dir, Path(image_path).stem, response_json)
                    logger.info(f"Successfully processed image: {image_path}")
                else:
                    self.save_output(self.fail_dir, Path(image_path).stem, {"error": "Invalid JSON response"})
                    logger.error(f"Invalid JSON response for image: {image_path}")
            except Exception as e:
                self.save_output(self.fail_dir, Path(image_path).stem, {"error": str(e)})
                logger.error(f"Failed to process image {image_path}: {str(e)}")

            # Update progress after each file is processed
            progress = int(((index + 1) / total_files) * 100)
            self.update_processing_status(StatusEnum.IN_PROGRESS, progress)
            logger.info(f"Progress updated to {progress}%")

        # Final update to mark as completed
        self.update_processing_status(StatusEnum.COMPLETED, 100, end_time=datetime.datetime.utcnow())
        logger.info("OCR processing completed successfully")

    def call_openai_api(self, image_path: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"Calling OpenAI API for image {image_path}")
        
        # Encode the image in base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare the payload for OpenAI API
        payload = {
            "model": "gpt-4o-mini",  # Adjust the model according to your needs
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What’s in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300  # Adjust tokens as needed
        }

        response = requests.post(OPENAI_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON response: {str(e)}")
                return None
        else:
            logger.error(f"OpenAI API request failed with status code {response.status_code}: {response.text}")
            return None

    def save_output(self, output_dir: str, filename: str, data: Dict[str, Any]):
        logger.debug(f"Saving output to {output_dir} for file {filename}")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{filename}.json")
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"Output saved: {output_path}")
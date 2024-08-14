import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import openai
from sqlalchemy.orm import Session
from models.processing import ProcessingStatus, StatusEnum
from models.dashboard import Project
from loguru import logger

# Constants
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".tif", ".tiff"]
OPENAI_API_KEY = "your_openai_api_key_here"

# Configure OpenAI API key
openai.api_key = OPENAI_API_KEY

class OCRProcessor:
    def __init__(self, project_id: int, db: Session):
        self.db = db
        self.project = self.get_project(project_id)
        self.input_dir = f"projects/{self.project.directory_name}/input"
        self.success_dir = f"projects/{self.project.directory_name}/output/success"
        self.fail_dir = f"projects/{self.project.directory_name}/output/fail"
        self.prompt_file = os.path.join(self.input_dir, "prompt.md")
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

    def read_prompt(self) -> str:
        logger.debug(f"Reading prompt from {self.prompt_file}")
        if not os.path.exists(self.prompt_file):
            logger.error("Prompt file not found.")
            raise FileNotFoundError("Prompt file not found.")
        
        with open(self.prompt_file, "r", encoding="utf-8") as file:
            return file.read()

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
        prompt = self.read_prompt()

        total_files = len(images)
        logger.info(f"Total images found for processing: {total_files}")
        
        if total_files == 0:
            self.update_processing_status(StatusEnum.FAILED, 100, end_time=datetime.datetime.utcnow())
            logger.error("No images found for processing.")
            raise Exception("No images found for processing.")

        for index, image_path in enumerate(images):
            logger.info(f"Processing image {index + 1}/{total_files}: {image_path}")
            try:
                response_json = self.call_openai_api(image_path, prompt)
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

    def call_openai_api(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"Calling OpenAI API for image {image_path}")
        with open(image_path, "rb") as image_file:
            response = openai.Image.create(prompt=prompt, n=1, size="1024x1024", file=image_file)

        # Assuming the response returns a JSON-like structure
        try:
            return response.get("data", [])[0]
        except (KeyError, IndexError):
            logger.error(f"Unexpected response format from OpenAI API for image {image_path}")
            return None

    def save_output(self, output_dir: str, filename: str, data: Dict[str, Any]):
        logger.debug(f"Saving output to {output_dir} for file {filename}")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{filename}.json")
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"Output saved: {output_path}")
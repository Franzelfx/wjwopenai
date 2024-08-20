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
from services.validator import JSONValidator

# Constants
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".tif", ".tiff"]
OPENAI_API_KEY = "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"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MX_TOKENS = 3000

# Configure OpenAI API key
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

class OCRProcessor:
    _processors = {}  # Class-level dictionary to store processors by project_id

    def __init__(self, project_id: int, db: Session):
        self.db = db
        self.project_id = project_id
        self.project = self._get_project(project_id)
        self.input_dir = f"projects/{self.project.directory_name}/input"
        self.output_dir = f"projects/{self.project.directory_name}/output"
        self.prompt_file_path = f"prompt.md"
        self.processing_status = self._get_processing_status(project_id)
        self._stop_flag = False
        self.current_index = 0  # Track the current index for resuming

        logger.info(f"OCRProcessor initialized for project {self.project.directory_name}")

        # Store this instance in the class-level dictionary
        OCRProcessor._processors[project_id] = self

    @staticmethod
    def get_processor(project_id: int):
        return OCRProcessor._processors.get(project_id)

    def _get_project(self, project_id: int) -> Project:
        logger.debug(f"Fetching project with ID {project_id}")
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project with ID {project_id} not found")
            raise Exception(f"Project with ID {project_id} not found")
        return project

    def _get_processing_status(self, project_id: int) -> ProcessingStatus:
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

    def load_prompt_file(self) -> Optional[str]:
        if os.path.exists(self.prompt_file_path):
            logger.info(f"Loading prompt file from {self.prompt_file_path}")
            with open(self.prompt_file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            logger.warning(f"Prompt file not found at {self.prompt_file_path}")
            return None
        
    def process_images(self, resume: bool = False):
        images = self.list_image_files()
        total_files = len(images)
        logger.info(f"Total images found for processing: {total_files}")
        
        if total_files == 0:
            self.update_processing_status(StatusEnum.FAILED, 100, end_time=datetime.datetime.utcnow())
            logger.error("No images found for processing.")
            raise Exception("No images found for processing.")

        # Empty the output fail and success directories if not resuming
        if not resume:
            for sub_dir in ["fail", "success"]:
                full_output_dir = os.path.join(self.output_dir, sub_dir)
                for file in os.listdir(full_output_dir):
                    os.remove(os.path.join(full_output_dir, file))

        prompt_text = self.load_prompt_file()
        
        if not prompt_text:
            self.update_processing_status(StatusEnum.FAILED, 100, end_time=datetime.datetime.utcnow())
            logger.error("Prompt file not found. Stopping processing.")
            raise Exception("Prompt file not found.")

        for index in range(self.current_index, total_files):
            if self._stop_flag:
                logger.info("Processing has been stopped.")
                self.current_index = index  # Save the current index for resuming later
                progress = int((index / total_files) * 100)
                self.update_processing_status(StatusEnum.PAUSED, progress, end_time=None)
                return

            image_path = images[index]
            logger.info(f"Processing image {index + 1}/{total_files}: {image_path}")
            try:
                response_json = self.call_openai_api(image_path, prompt_text)
                if response_json:
                    content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if JSONValidator.is_valid_json(content):
                        JSONValidator.save_cleaned_json(self.output_dir, Path(image_path).stem, content.encode('utf-8'), success=True)
                        logger.info(f"Successfully processed and saved JSON for image: {image_path}")
                    else:
                        JSONValidator.save_cleaned_json(self.output_dir, Path(image_path).stem, content.encode('utf-8'), success=False)
                        logger.error(f"Invalid JSON content for image: {image_path}")
                else:
                    JSONValidator.save_cleaned_json(self.output_dir, Path(image_path).stem, None, success=False)
                    logger.error(f"Invalid JSON response for image: {image_path}")
            except Exception as e:
                JSONValidator.save_cleaned_json(self.output_dir, Path(image_path).stem, None, success=False)
                logger.error(f"Failed to process image {image_path}: {str(e)}")

            progress = int(((index + 1) / total_files) * 100)
            self.update_processing_status(StatusEnum.IN_PROGRESS, progress)
            logger.info(f"Progress updated to {progress}%")

        self.update_processing_status(StatusEnum.COMPLETED, 100, end_time=datetime.datetime.utcnow())
        logger.info("OCR processing completed successfully")

    def call_openai_api(self, image_path: str, prompt_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
        logger.debug(f"Calling OpenAI API for image {image_path}")
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": MX_TOKENS,
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

    def stop_processing(self):
        logger.info("Stopping the OCR process.")
        self._stop_flag = True

    def resume_processing(self):
        logger.info("Resuming the OCR process.")
        self._stop_flag = False
        self.process_images(resume=True)

import os
import json
import datetime
import base64
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger
import numpy as np
from models.processing import ProcessingStatus, StatusEnum
from models.dashboard import Project
from dotenv import load_dotenv
from tqdm import tqdm
import tiktoken
import chromadb
import uuid
from chromadb.config import Settings
import random
import time
import aiohttp
import asyncio


# Load environment variables from .env
load_dotenv()

# Existing constants
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".tif", ".tiff"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
MX_TOKENS = int(os.getenv("MX_TOKENS", 10000))
VECTOR_STORE_INPUT_PATH = os.getenv("VECTOR_STORE_INPUT_PATH", "./tools/geodata/json")
VECTOR_STORE_OUTPUT_PATH = os.getenv("VECTOR_STORE_OUTPUT_PATH", "./vector_store")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
INITIAL_BACKOFF = int(os.getenv("INITIAL_BACKOFF", 1))
MAX_BACKOFF = int(os.getenv("MAX_BACKOFF", 32))

# New parameters for OpenAI API
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
TOP_P = float(os.getenv("TOP_P", 1.0))
FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", 0.0))
PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", 0.0))


# Ensure VECTOR_STORE_INPUT_PATH is set
if not VECTOR_STORE_INPUT_PATH:
    raise ValueError("VECTOR_STORE_INPUT_PATH is not set. Please ensure the .env file contains this variable.")

# Configure OpenAI API key
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

import chromadb


class OCRProcessor:
    def __init__(self, project_id: int, db: Session):
        """
        Initialize the OCRProcessor with a project ID and database session.
        This uses a persistent Chroma client.
        """
        self.db = db
        self.project_id = project_id
        self.project = self._get_project(project_id)
        self.input_dir = f"projects/{self.project.directory_name}/input"
        self.output_dir = f"projects/{self.project.directory_name}/output"
        self.processing_status = self._get_processing_status(project_id)
        self._stop_flag = False
        self.current_index = 0  # Track the current index for resuming

        # Initialize Chroma persistent client
        self.client = chromadb.PersistentClient(path=VECTOR_STORE_OUTPUT_PATH)  # Use the environment variable for persistence path

        self.collection_name = f"project_{self.project_id}_embeddings"

        try:
            # Try to get the collection, if it doesn't exist, create it
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]

            if self.collection_name in collection_names:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Found existing ChromaDB collection: {self.collection_name}")
            else:
                self.collection = self.client.create_collection(self.collection_name)
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collection for project {self.project_id}: {str(e)}")
            raise Exception(f"Failed to initialize ChromaDB collection for project {self.project_id}")

        logger.info(f"OCRProcessor initialized for project {self.project.directory_name}")


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

    def chunk_text(self, text: str, max_tokens: int) -> List[str]:
        """
        Split a large text into chunks that fit within the token limit of the model.
        """
        tokenizer = tiktoken.get_encoding("cl100k_base")  # Use appropriate tokenizer for counting tokens
        tokens = tokenizer.encode(text)
        
        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks

    def generate_vector_store(self):
        """Generate a Chroma vector store by processing addresses from JSON files."""
        concatenated_addresses = ""
        json_files = [os.path.join(root, file) for root, _, files in os.walk(VECTOR_STORE_INPUT_PATH) for file in files if file.endswith(".json")]

        if not json_files:
            logger.error("No JSON files found in the input directory.")
            return

        # Read JSON files and concatenate addresses
        for file_path in tqdm(json_files, desc="Processing JSON files", unit="file"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            address = item.get("Address", "N/A")
                            if address != "N/A":
                                concatenated_addresses += address + ", "
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON file {file_path}: {str(e)}")

        # Trim trailing comma and space
        concatenated_addresses = concatenated_addresses.rstrip(", ")

        if concatenated_addresses:
            # Chunk and embed text
            chunks = self.chunk_text(concatenated_addresses, MAX_TOKENS)
            for chunk in tqdm(chunks, desc="Generating embeddings", unit="chunk"):
                embedding = self.get_text_embedding(chunk)
                if embedding is not None:
                    # Generate a unique ID for each embedding
                    unique_id = str(uuid.uuid4())
                    
                    # Add embedding, document, and ID to Chroma collection
                    self.collection.add(embeddings=[embedding], documents=[chunk], ids=[unique_id])
                    logger.info(f"Added chunk embeddings to project {self.project_id}'s Chroma vector store with ID {unique_id}.")

    def get_text_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embeddings using OpenAI API with retries and exponential backoff."""
        payload = {
            "model": "text-embedding-ada-002",
            "input": text,
        }

        retry_count = 0
        backoff = INITIAL_BACKOFF  # Initial backoff time

        while retry_count < MAX_RETRIES:
            try:
                response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    embedding = response.json().get("data", [])[0].get("embedding", [])
                    if embedding:
                        return embedding
                    else:
                        logger.error("Failed to extract embedding from response.")
                else:
                    logger.error(f"OpenAI API request failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error during API call: {str(e)}")

            # If we reach here, the request failed. Apply exponential backoff
            retry_count += 1
            if retry_count < MAX_RETRIES:
                sleep_time = min(backoff, MAX_BACKOFF)
                logger.info(f"Retrying in {sleep_time} seconds (Attempt {retry_count}/{MAX_RETRIES})...")
                time.sleep(sleep_time)
                backoff *= 2  # Exponentially increase backoff
                backoff += random.uniform(0, 1)  # Add jitter to avoid synchronization issues

        logger.error(f"Failed to get embedding after {MAX_RETRIES} attempts.")
        return None

    def query_vector_store(self, query: str, n_results: int = 5):
        """Query the project-specific Chroma vector store."""
        embedding = self.get_text_embedding(query)
        if embedding:
            results = self.collection.query(query_embeddings=[embedding], n_results=n_results)
            return results.get('documents', [])
        return []

    async def call_openai_api(self, image_path: str, prompt_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call the OpenAI API for image processing with retries and exponential backoff."""
        logger.debug(f"Calling OpenAI API for image {image_path}")
        async with aiohttp.ClientSession() as session:
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
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
                "frequency_penalty": FREQUENCY_PENALTY,
                "presence_penalty": PRESENCE_PENALTY,
            }

            retry_count = 0
            backoff = INITIAL_BACKOFF  # Initial backoff time

            while retry_count < MAX_RETRIES:
                # Check if stop flag is set before each retry
                if self._stop_flag:
                    logger.info("Processing has been stopped before making the API call.")
                    return None

                try:
                    async with session.post(OPENAI_API_URL, headers=headers, json=payload) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"OpenAI API request failed: {response.status} - {await response.text()}")

                except Exception as e:
                    logger.error(f"Error during OpenAI API call for image {image_path}: {str(e)}")

                # If the request fails, apply exponential backoff before retrying
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    sleep_time = min(backoff, MAX_BACKOFF)
                    logger.info(f"Retrying in {sleep_time} seconds (Attempt {retry_count}/{MAX_RETRIES})...")

                    # Check if stop flag is set before sleeping
                    if self._stop_flag:
                        logger.info("Processing has been stopped during the retry wait period.")
                        return None

                    await asyncio.sleep(sleep_time)
                    backoff *= 2  # Exponentially increase the backoff
                    backoff += random.uniform(0, 1)  # Add jitter to the backoff time

            logger.error(f"Failed to process image {image_path} after {MAX_RETRIES} attempts.")
            return None


    async def process_images(self, resume: bool = False):
        images = self.list_image_files()
        total_files = len(images)
        logger.info(f"Total images found for processing: {total_files}")
        
        if total_files == 0:
            self.update_processing_status(StatusEnum.FAILED, 100, end_time=datetime.datetime.utcnow())
            logger.error("No images found for processing.")
            raise Exception("No images found for processing.")

        # Prompt text is in file "backend/prompt.md"
        prompt_text = ""
        with open("./prompt.md", "r") as f:
            prompt_text = f.read()

        for index in range(self.current_index, total_files):
            if self._stop_flag:
                logger.info("Processing has been stopped.")
                self.current_index = index  # Save the current index for resuming later
                progress = int((index / total_files) * 100)
                self.update_processing_status(StatusEnum.PAUSED, progress, end_time=None)
                return

            image_path = images[index]
            logger.info(f"Processing image {index + 1}/{total_files}: {image_path}")

            response_json = await self.call_openai_api(image_path, prompt_text)
            if self._stop_flag:
                logger.info("Processing has been stopped after the API call.")
                self.current_index = index
                progress = int((index / total_files) * 100)
                self.update_processing_status(StatusEnum.PAUSED, progress, end_time=None)
                return

            if response_json:
                content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    output_file = os.path.join(self.output_dir, f"{Path(image_path).stem}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(content, f)
                    logger.info(f"Successfully processed and saved JSON for image: {image_path}")
                else:
                    logger.error(f"Invalid content for image: {image_path}")

            progress = int(((index + 1) / total_files) * 100)
            self.update_processing_status(StatusEnum.IN_PROGRESS, progress)
            logger.info(f"Progress updated to {progress}%")

        self.update_processing_status(StatusEnum.COMPLETED, 100, end_time=datetime.datetime.utcnow())
        logger.info("OCR processing completed successfully")

    @staticmethod
    def get_processor(project_id: int, db: Session) -> 'OCRProcessor':
        """
        Retrieves the processor for a given project ID.
        In this example, we're creating a new instance for simplicity.
        If you need to retrieve an existing processor, you would adjust this accordingly.
        """
        return OCRProcessor(project_id, db)

    def stop_processing(self):
        logger.info("Stopping the OCR process.")
        self._stop_flag = True

    def stop_processing(self):
        logger.info("Stopping the OCR process.")
        self._stop_flag = True


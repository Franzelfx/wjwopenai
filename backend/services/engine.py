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
    _instances: dict[int, "OCRProcessor"] = {}
    
    def __init__(self, project_id: int, db: Session):
        """
        Initialize the OCRProcessor with a project ID and database session.
        This uses a persistent Chroma client and remembers the project-specific
        prompt markdown path.
        """
        OCRProcessor._instances[project_id] = self
        self.db = db
        self.project_id = project_id

        # load project info and file-tree roots
        self.project = self._get_project(project_id)
        self.input_dir  = os.path.join("projects", self.project.directory_name, "input")
        self.output_dir = os.path.join("projects", self.project.directory_name, "output")
        self.processing_status = self._get_processing_status(project_id)

        # track interruption and resume index
        self._stop_flag    = False
        self.current_index = 0

        # ▶── NEW: path to the project's prompt markdown
        #    stored in Project.prompt_md (filename) or defaults to "prompt.md"
        self.prompt_path = os.path.join(
            "projects",
            self.project.directory_name,
            self.project.prompt_md or "prompt.md"
        )

        # initialize ChromaDB client & collection
        self.client = chromadb.PersistentClient(path=VECTOR_STORE_OUTPUT_PATH)
        self.collection_name = f"project_{self.project_id}_embeddings"
        try:
            existing = [c.name for c in self.client.list_collections()]
            if self.collection_name in existing:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Found ChromaDB collection: {self.collection_name}")
            else:
                self.collection = self.client.create_collection(self.collection_name)
                logger.info(f"Created ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"ChromaDB init failed for project {project_id}: {e}")
            raise

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
        
    def _handle_api_response(
        self,
        image_path: str,
        response_json: Dict[str, Any] | None,
        success_dir: str,
        fail_dir: str,
    ) -> None:
        """
        Save the model response exactly like the original implementation:
        * Valid JSON  → output/success/<stem>.json
        * Anything else → output/fail/<stem>.json with an error wrapper.
        """
        stem = Path(image_path).stem
        fail_path = Path(fail_dir, f"{stem}.json")

        # nothing / HTTP error
        if response_json is None:
            with open(fail_path, "w", encoding="utf-8") as f:
                json.dump({"error": "No response from API"}, f, indent=4, ensure_ascii=False)
            logger.error(f"No response for {image_path}")
            return

        # get text content
        content = (
            response_json.get("choices", [{}])[0]
                       .get("message", {})
                       .get("content", "")
        )

        # empty
        if not content:
            with open(fail_path, "w", encoding="utf-8") as f:
                json.dump({"error": "Empty content"}, f, indent=4, ensure_ascii=False)
            logger.error(f"Empty content for {image_path}")
            return

        # --------- clean up markdown fences ----------
        for fence in ("```json", "```", "```JSON", "```Json"):
            content = content.replace(fence, "")
        content = content.strip()

        # sometimes the assistant wraps JSON in text; grab the first { … }
        if content and content[0] != "{":
            first = content.find("{")
            last  = content.rfind("}")
            if first != -1 and last != -1 and last > first:
                content = content[first : last + 1]

        # ---------- try to parse ----------------------
        try:
            parsed = json.loads(content)
            ok_path = Path(success_dir, f"{stem}.json")
            with open(ok_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved valid JSON to {ok_path}")

        except Exception as exc:
            # still invalid → save raw text to fail dir
            with open(fail_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"error": "Invalid JSON format", "message": content},
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
            logger.error(f"Invalid JSON for {image_path}: {exc}")

    async def process_images(self, resume: bool = False) -> None:
        """
        Main OCR loop.  Stops cleanly on self._stop_flag and leaves the
        processor alive so it can be resumed; closes itself only when
        the run really finishes (COMPLETED / FAILED).
        """
        images = self.list_image_files()
        total = len(images)
        if total == 0:
            self.update_processing_status(StatusEnum.FAILED, 100,
                                          end_time=datetime.datetime.utcnow())
            self.close()
            raise Exception("No images found for processing.")

        # output dirs
        success_dir = os.path.join(self.output_dir, "success")
        fail_dir    = os.path.join(self.output_dir, "fail")
        os.makedirs(success_dir, exist_ok=True)
        os.makedirs(fail_dir,    exist_ok=True)

        # prompt (project specific)
        if os.path.isfile(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as fh:
                prompt_text = fh.read()
            logger.info(f"Prompt loaded from {self.prompt_path}")
        else:
            prompt_text = ""
            logger.warning(f"No prompt at {self.prompt_path}")

        start_idx = self.current_index if resume else 0

        for idx in range(start_idx, total):

            # -------- handle external stop/pause request -------------
            if self._stop_flag:
                pct = int(idx / total * 100)
                self.current_index = idx
                self.update_processing_status(StatusEnum.PAUSED, pct)
                logger.info(f"Paused at {pct}% (index {idx})")
                return                               # keep instance alive

            img_path = images[idx]
            logger.info(f"[{idx+1}/{total}] {img_path}")

            try:
                resp = await self.call_openai_api(img_path, prompt_text)

                # stop pressed while API call in flight
                if self._stop_flag:
                    pct = int(idx / total * 100)
                    self.current_index = idx
                    self.update_processing_status(StatusEnum.PAUSED, pct)
                    logger.info(f"Paused after call at {pct}%")
                    return

                self._handle_api_response(img_path, resp, success_dir, fail_dir)

            except Exception as exc:
                logger.exception(f"Unhandled error on {img_path}: {exc}")
                self._handle_api_response(img_path, None, success_dir, fail_dir)

            # progress update (only if not pausing)
            pct = int((idx + 1) / total * 100)
            self.update_processing_status(StatusEnum.IN_PROGRESS, pct)

        # ---------- finished normally -------------------------------
        self.update_processing_status(StatusEnum.COMPLETED, 100,
                                      end_time=datetime.datetime.utcnow())
        self.close()          # unregister processor
        logger.info("OCR processing completed")

    @staticmethod
    def get_processor(project_id: int) -> "OCRProcessor | None":
        return OCRProcessor._instances.get(project_id)

    def close(self):
        OCRProcessor._instances.pop(self.project_id, None)

    def stop_processing(self):
        self._stop_flag = True
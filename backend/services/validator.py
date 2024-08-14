import os
import json
from typing import Dict, Any
from loguru import logger
from pathlib import Path
import re

class JSONValidator:
    @staticmethod
    def clean_json_content(content: str) -> str:
        """
        Cleans the JSON content by removing unnecessary characters, such as code block markers.
        :param content: The JSON string to be cleaned.
        :return: A cleaned JSON string.
        """
        # Remove common JSON code block markers (like ```json ... ```)
        content = re.sub(r'```json\s*|\s*```', '', content)

        # Trim leading and trailing whitespace
        content = content.strip()

        return content

    @staticmethod
    def is_valid_json(content: str) -> bool:
        """
        Validates if the given content is a valid JSON string after cleaning.
        :param content: The string to be validated as JSON.
        :return: True if valid JSON, False otherwise.
        """
        try:
            cleaned_content = JSONValidator.clean_json_content(content)
            json.loads(cleaned_content)
            return True
        except ValueError as e:
            logger.error(f"Invalid JSON content: {str(e)}")
            return False

    @staticmethod
    def save_cleaned_json(output_dir: str, filename: str, content: str):
        """
        Saves only the cleaned JSON content to the output directory.
        :param output_dir: The base directory for output files.
        :param filename: The name of the file to save.
        :param content: The JSON content to be saved.
        """
        cleaned_content = JSONValidator.clean_json_content(content)
        
        # Convert the cleaned content back to a dictionary to save it as a JSON file
        json_data = json.loads(cleaned_content)

        # Determine the directory to save the cleaned JSON
        full_output_dir = os.path.join(output_dir, "success")
        
        # Ensure the directory exists
        os.makedirs(full_output_dir, exist_ok=True)
        
        # Create the full path for the file
        output_path = os.path.join(full_output_dir, f"{filename}.json")
        
        # Save the cleaned JSON data
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, indent=4)
        
        logger.info(f"Cleaned JSON saved to {output_path}")
